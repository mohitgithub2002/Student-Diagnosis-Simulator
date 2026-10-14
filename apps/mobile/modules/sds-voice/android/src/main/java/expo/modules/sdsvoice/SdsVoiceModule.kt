package expo.modules.sdsvoice

import android.Manifest
import android.app.ActivityManager
import android.content.Context
import android.content.pm.PackageManager
import android.view.WindowManager
import expo.modules.interfaces.permissions.Permissions
import expo.modules.kotlin.Promise
import expo.modules.kotlin.exception.CodedException
import expo.modules.kotlin.exception.Exceptions
import expo.modules.kotlin.functions.Coroutine
import expo.modules.kotlin.modules.Module
import expo.modules.kotlin.modules.ModuleDefinition
import expo.modules.kotlin.records.Field
import expo.modules.kotlin.records.Record
import java.io.File
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class StartOptions : Record {
  @Field val modelPath: String? = null
}

internal class NotRecordingException : CodedException("ERR_NOT_RECORDING", "No voice capture in progress", null)

/**
 * On-device voice for the Android app (FR-11): microphone energy levels and offline Vosk speech-to-text.
 * Audio stays in memory; JS receives only numbers and recognised words, and turns them into features.
 */
class SdsVoiceModule : Module() {
  private val context: Context
    get() = appContext.reactContext ?: throw Exceptions.ReactContextLost()

  private var store: ModelStore? = null

  @Volatile private var capture: Capture? = null

  private fun models(): ModelStore = store ?: ModelStore(File(context.filesDir, "vosk")).also { store = it }

  override fun definition() = ModuleDefinition {
    Name("SdsVoice")

    Events("onLevel", "onModelProgress")

    AsyncFunction("getPermissionsAsync") { promise: Promise ->
      Permissions.getPermissionsWithPermissionsManager(appContext.permissions, promise, Manifest.permission.RECORD_AUDIO)
    }

    AsyncFunction("requestPermissionsAsync") { promise: Promise ->
      Permissions.askForPermissionsWithPermissionsManager(appContext.permissions, promise, Manifest.permission.RECORD_AUDIO)
    }

    AsyncFunction("start") { options: StartOptions ->
      if (context.checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
        throw Exceptions.MissingPermissions(Manifest.permission.RECORD_AUDIO)
      }
      cancelCapture()
      val path = options.modelPath?.takeIf { sttFitsInMemory() }
      val modelStore = models()
      val next = Capture(path?.let { p -> { modelStore.newRecognizer(p, Capture.RATE.toFloat()) } }) { level ->
        emit("onLevel", mapOf("level" to level.toDouble()))
      }
      next.start()
      capture = next
      keepScreenOn(true) // Android silences the microphone once the screen turns off
      mapOf("stt" to (path != null))
    }

    AsyncFunction("stop") Coroutine { ->
      val current = capture ?: throw NotRecordingException()
      capture = null
      keepScreenOn(false)
      withContext(Dispatchers.IO) { current.stop(drainMs = 5_000) }
    }

    AsyncFunction<Unit>("cancel") {
      cancelCapture()
    }

    AsyncFunction("modelPath") { name: String ->
      models().installedPath(name)
    }

    AsyncFunction("preloadModel") Coroutine { path: String ->
      withContext(Dispatchers.IO) {
        if (sttFitsInMemory()) {
          models().preload(path)
          true
        } else {
          false
        }
      }
    }

    AsyncFunction("installModel") Coroutine { name: String, url: String, sha256: String ->
      withContext(Dispatchers.IO) {
        models().install(name, url, sha256) { received, total ->
          emit("onModelProgress", mapOf("name" to name, "received" to received.toDouble(), "total" to total.toDouble()))
        }
      }
    }

    AsyncFunction<Unit>("releaseModels") {
      store?.release()
    }

    OnActivityEntersBackground {
      cancelCapture() // background apps get silence from the microphone anyway
    }

    OnDestroy {
      cancelCapture()
      store?.release()
    }
  }

  private fun cancelCapture() {
    capture?.cancel()
    capture = null
    keepScreenOn(false)
  }

  /** Events come from worker threads and may outlive the JS runtime; a lost event must never crash the app. */
  private fun emit(name: String, body: Map<String, Any?>) {
    try {
      sendEvent(name, body)
    } catch (_: Exception) {
    }
  }

  private fun keepScreenOn(on: Boolean) {
    val activity = runCatching { appContext.currentActivity }.getOrNull() ?: return
    activity.runOnUiThread {
      if (on) {
        activity.window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
      } else {
        activity.window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
      }
    }
  }

  /** Speech-to-text needs a few hundred MB; low-memory phones get energy-only features instead. */
  private fun sttFitsInMemory(): Boolean {
    val am = context.getSystemService(ActivityManager::class.java) ?: return false
    val info = ActivityManager.MemoryInfo().also { am.getMemoryInfo(it) }
    return !am.isLowRamDevice && !info.lowMemory && info.totalMem >= 2_500_000_000L
  }
}
