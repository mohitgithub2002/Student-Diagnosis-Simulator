package expo.modules.sdsvoice

import android.annotation.SuppressLint
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import expo.modules.kotlin.exception.CodedException
import expo.modules.sdsvoice.core.FloatList
import expo.modules.sdsvoice.core.Framer
import expo.modules.sdsvoice.core.Pcm
import java.util.concurrent.ArrayBlockingQueue
import java.util.concurrent.TimeUnit
import kotlin.concurrent.thread
import org.vosk.Recognizer

internal class MicUnavailableException(cause: Throwable? = null) :
  CodedException("ERR_MIC_UNAVAILABLE", "The microphone could not be opened", cause)

/**
 * One microphone session. Audio is read into memory in 100 ms chunks and turned into numbers: an energy
 * level per 20 ms frame and, when a model is given, Vosk results with word timings. The samples are dropped
 * as soon as they are processed; nothing is written to storage or sent anywhere.
 *
 * The reader thread never waits for the recogniser: chunks go through a bounded queue, and if speech-to-text
 * falls too far behind (or the model fails to load) it is dropped for this capture while the energy levels
 * carry on, so the answer still gets timing features.
 */
internal class Capture(
  private val recognizer: (() -> Recognizer)?,
  private val onLevel: (Float) -> Unit,
) {
  companion object {
    const val RATE = 16_000
    const val FRAME = 320 // 20 ms
    const val CHUNK = 1_600 // 100 ms
    const val MAX_SECONDS = 300
    const val MAX_BACKLOG = 600 // 60 s of audio waiting for the recogniser
    private val END = ShortArray(0)
  }

  private val levels = FloatList()
  private val queue = ArrayBlockingQueue<ShortArray>(MAX_BACKLOG)
  private val results = ArrayList<String>() // Vosk JSON, touched only by the recogniser thread until it ends

  @Volatile private var running = false
  @Volatile private var dropped: String? = null
  @Volatile private var samples = 0L
  private var record: AudioRecord? = null
  private var reader: Thread? = null
  private var stt: Thread? = null

  @SuppressLint("MissingPermission") // the module checks RECORD_AUDIO before creating a capture
  fun start() {
    val min = AudioRecord.getMinBufferSize(RATE, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT)
    if (min <= 0) throw MicUnavailableException()
    val rec = try {
      AudioRecord(
        MediaRecorder.AudioSource.VOICE_RECOGNITION, RATE, AudioFormat.CHANNEL_IN_MONO,
        AudioFormat.ENCODING_PCM_16BIT, maxOf(min, CHUNK * 2 * 4),
      )
    } catch (e: Exception) {
      throw MicUnavailableException(e)
    }
    if (rec.state != AudioRecord.STATE_INITIALIZED) {
      rec.release()
      throw MicUnavailableException()
    }
    try {
      rec.startRecording()
    } catch (e: IllegalStateException) {
      rec.release()
      throw MicUnavailableException(e)
    }
    if (rec.recordingState != AudioRecord.RECORDSTATE_RECORDING) {
      rec.release()
      throw MicUnavailableException()
    }
    record = rec
    running = true
    // The model loads on the recogniser thread while audio already queues up from the first sample, so
    // word times and energy frames share one clock.
    recognizer?.let { make -> stt = thread(name = "sds-voice-stt") { recognise(make) } }
    reader = thread(name = "sds-voice-read", priority = Thread.MAX_PRIORITY) { read(rec) }
  }

  private fun read(rec: AudioRecord) {
    val framer = Framer(FRAME) { levels.add(it) }
    try {
      while (running && samples < RATE.toLong() * MAX_SECONDS) {
        val chunk = ShortArray(CHUNK)
        val n = rec.read(chunk, 0, CHUNK)
        if (n < 0) break
        if (n == 0) continue
        framer.push(chunk, n)
        samples += n
        onLevel(Pcm.rms(chunk, 0, n))
        if (stt != null && dropped == null && !queue.offer(if (n == CHUNK) chunk else chunk.copyOf(n))) {
          dropped = "backlog"
          queue.clear()
        }
      }
    } finally {
      try {
        rec.stop()
      } catch (_: IllegalStateException) {
      }
      rec.release()
    }
  }

  private fun recognise(make: () -> Recognizer) {
    val rec = try {
      make()
    } catch (e: Throwable) { // a missing or broken model, or the native library failing to load
      if (dropped == null) dropped = "model"
      queue.clear()
      return
    }
    rec.use {
      it.setWords(true)
      while (dropped == null) {
        val chunk = queue.poll(250, TimeUnit.MILLISECONDS) ?: if (running) continue else break
        if (chunk === END) break
        if (it.acceptWaveForm(chunk, chunk.size)) results.add(it.result)
      }
      if (dropped == null) results.add(it.finalResult)
    }
  }

  /** Closes the microphone and returns the energy levels and, if speech-to-text kept up, the Vosk results. */
  fun stop(drainMs: Long): Map<String, Any?> {
    running = false
    stopRecord()
    reader?.join(2_000)
    stt?.let { worker ->
      queue.offer(END)
      worker.join(drainMs)
      if (worker.isAlive && dropped == null) dropped = "timeout"
    }
    val sttOk = stt != null && dropped == null
    return mapOf(
      "levels" to levels.toArray(),
      "frameMs" to FRAME * 1000 / RATE,
      "durationMs" to samples * 1000.0 / RATE,
      "results" to if (sttOk) ArrayList(results) else null,
      "sttDropped" to if (stt == null) null else dropped,
      "inputSilent" to levels.allZero(),
    )
  }

  fun cancel() {
    dropped = "cancelled"
    running = false
    queue.clear()
    stopRecord()
  }

  private fun stopRecord() {
    try {
      record?.stop() // unblocks the reader, which releases the recorder
    } catch (_: IllegalStateException) {
    }
  }
}
