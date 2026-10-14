package expo.modules.sdsvoice

import expo.modules.sdsvoice.core.ModelArchive
import java.io.File
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import org.vosk.LibVosk
import org.vosk.LogLevel
import org.vosk.Model
import org.vosk.Recognizer

/**
 * Speech models in the app's private files folder (`files/vosk/<name>`). Models are public data downloaded
 * from the school's server; no student data is stored here. One model is kept loaded at a time.
 */
internal class ModelStore(private val root: File) {
  private val name = Regex("[A-Za-z0-9._-]+")
  private val installLock = Any()
  private var loaded: Model? = null
  private var loadedPath: String? = null

  private fun dir(model: String): File {
    if (!name.matches(model)) throw IOException("Invalid model name")
    return File(root, model)
  }

  fun installedPath(model: String): String? = dir(model).takeIf { ModelArchive.isModel(it) }?.absolutePath

  /** Loads the model now so the first answer doesn't wait for it. */
  @Synchronized
  fun preload(path: String) {
    model(path)
  }

  /** Creates a recogniser under the same lock as [release], so a model is never freed between the two steps. */
  @Synchronized
  fun newRecognizer(path: String, sampleRate: Float): Recognizer = Recognizer(model(path), sampleRate)

  private fun model(path: String): Model {
    loaded?.let { if (loadedPath == path) return it }
    release()
    LibVosk.setLogLevel(LogLevel.WARNINGS)
    return Model(path).also {
      loaded = it
      loadedPath = path
    }
  }

  /** Frees the loaded model. Vosk counts references, so a recogniser still running keeps its copy alive. */
  @Synchronized
  fun release() {
    loaded?.close()
    loaded = null
    loadedPath = null
  }

  /** Downloads, checks and unpacks a model; returns its folder. Temporary files are removed on any failure. */
  fun install(model: String, url: String, sha256: String, progress: (Long, Long) -> Unit): String {
    synchronized(installLock) {
      val existing = installedPath(model)
      if (existing != null) return existing
      if (!root.isDirectory && !root.mkdirs()) throw IOException("Cannot create $root")
      val part = File(root, "$model.zip.part")
      val staging = File(root, "$model.partial")
      val target = dir(model)
      try {
        download(url, part, progress)
        if (!ModelArchive.sha256Hex(part).equals(sha256, ignoreCase = true)) throw IOException("Checksum mismatch for $model")
        staging.deleteRecursively()
        part.inputStream().use { ModelArchive.extract(it, staging) }
        val modelRoot = ModelArchive.findModelRoot(staging) ?: throw IOException("$model is not a speech model")
        target.deleteRecursively()
        if (!modelRoot.renameTo(target)) throw IOException("Cannot install $model")
        return target.absolutePath
      } finally {
        part.delete()
        staging.deleteRecursively()
      }
    }
  }

  private fun download(url: String, dest: File, progress: (Long, Long) -> Unit) {
    val parsed = URL(url)
    if (parsed.protocol != "https" && parsed.protocol != "http") throw IOException("Unsupported model URL")
    val conn = parsed.openConnection() as HttpURLConnection
    conn.connectTimeout = 15_000
    conn.readTimeout = 30_000
    try {
      if (conn.responseCode !in 200..299) throw IOException("Model download failed: HTTP ${conn.responseCode}")
      val total = conn.contentLengthLong
      if (total > ModelArchive.MAX_BYTES) throw IOException("Model is too large")
      // Room for the archive and the unpacked model, with a margin.
      if (total > 0 && root.usableSpace < total * 4) throw IOException("Not enough free space for the speech model")
      var received = 0L
      var lastStep = -1L
      conn.inputStream.use { input ->
        dest.outputStream().use { out ->
          val buf = ByteArray(64 * 1024)
          while (true) {
            val n = input.read(buf)
            if (n < 0) break
            out.write(buf, 0, n)
            received += n
            if (received > ModelArchive.MAX_BYTES) throw IOException("Model is too large")
            val step = if (total > 0) received * 100 / total else received shr 20 // percent, or per MB
            if (step != lastStep) {
              lastStep = step
              progress(received, total)
            }
          }
        }
      }
    } finally {
      conn.disconnect()
    }
  }
}
