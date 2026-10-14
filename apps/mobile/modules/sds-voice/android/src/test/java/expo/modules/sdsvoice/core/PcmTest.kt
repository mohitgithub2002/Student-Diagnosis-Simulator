package expo.modules.sdsvoice.core

import kotlin.math.PI
import kotlin.math.roundToInt
import kotlin.math.sin
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class PcmTest {
  @Test
  fun rmsMatchesTheWebScale() {
    assertEquals(0f, Pcm.rms(ShortArray(320)), 0f)
    assertEquals(0.5f, Pcm.rms(ShortArray(320) { 16384 }), 1e-6f)
    val sine = ShortArray(1600) { (0.5 * 32768 * sin(2 * PI * 440 * it / 16000)).roundToInt().toShort() }
    assertEquals(0.3536f, Pcm.rms(sine), 1e-3f)
    assertEquals(0f, Pcm.rms(ShortArray(4), 0, 0), 0f)
  }

  @Test
  fun framerCutsFramesAcrossOddReads() {
    val levels = mutableListOf<Float>()
    val framer = Framer(320) { levels.add(it) }
    val loud = ShortArray(333) { 16384 }
    repeat(3) { framer.push(loud, loud.size) } // 999 samples: three whole frames, 39 left over
    assertEquals(3, levels.size)
    framer.push(ShortArray(280), 280) // 39 + 280 = 319: one sample short of a frame
    assertEquals(3, levels.size)
    framer.push(ShortArray(1), 1) // completes the fourth frame: 39 loud + 281 quiet
    assertEquals(4, levels.size)
    assertTrue(levels[3] > 0f && levels[3] < 0.5f)
    framer.push(loud, 10) // only the first n samples of a read count
    assertEquals(4, levels.size)
  }

  @Test
  fun floatListGrowsAndDetectsSilence() {
    val list = FloatList(2)
    assertFalse(list.allZero()) // nothing captured is not the same as silence
    repeat(5) { list.add(0f) }
    assertTrue(list.allZero())
    list.add(0.01f)
    assertFalse(list.allZero())
    assertEquals(6, list.toArray().size)
  }
}
