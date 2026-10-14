package expo.modules.sdsvoice.core

import kotlin.math.sqrt

/** Audio maths with no Android classes, so it runs in plain JVM unit tests. */
object Pcm {
  /** Root mean square of 16-bit samples scaled to [-1, 1], the scale the web app measures in. */
  fun rms(buf: ShortArray, from: Int = 0, len: Int = buf.size): Float {
    if (len <= 0) return 0f
    var sum = 0.0
    for (i in from until from + len) {
      val s = buf[i] / 32768.0
      sum += s * s
    }
    return sqrt(sum / len).toFloat()
  }
}

/** Cuts a stream of samples into fixed-size frames, whatever the read sizes, and reports each frame's RMS. */
class Framer(private val frameSize: Int, private val onFrame: (Float) -> Unit) {
  private val pending = ShortArray(frameSize)
  private var filled = 0

  fun push(buf: ShortArray, n: Int) {
    var i = 0
    while (i < n) {
      val take = minOf(frameSize - filled, n - i)
      System.arraycopy(buf, i, pending, filled, take)
      filled += take
      i += take
      if (filled == frameSize) {
        onFrame(Pcm.rms(pending, 0, frameSize))
        filled = 0
      }
    }
  }
}

/** A growable list of floats without boxing. */
class FloatList(initial: Int = 1024) {
  private var data = FloatArray(initial)
  var size = 0
    private set

  fun add(v: Float) {
    if (size == data.size) data = data.copyOf(data.size * 2)
    data[size++] = v
  }

  fun toArray(): FloatArray = data.copyOf(size)

  /** True when frames were captured and every one is exactly zero (Android's microphone privacy switch). */
  fun allZero(): Boolean {
    for (i in 0 until size) if (data[i] != 0f) return false
    return size > 0
  }
}
