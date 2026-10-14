package expo.modules.sdsvoice.core

import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.File
import java.io.IOException
import java.nio.file.Files
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class ModelArchiveTest {
  private fun zip(vararg entries: Pair<String, ByteArray?>): ByteArray {
    val out = ByteArrayOutputStream()
    ZipOutputStream(out).use { z ->
      for ((name, data) in entries) {
        z.putNextEntry(ZipEntry(name))
        if (data != null) z.write(data)
        z.closeEntry()
      }
    }
    return out.toByteArray()
  }

  private fun tempDir(): File = Files.createTempDirectory("sds-voice").toFile()

  @Test
  fun extractsAnOfficialModelLayout() {
    val dest = tempDir()
    val archive = zip(
      "vosk-model-small-en-in-0.4/" to null,
      "vosk-model-small-en-in-0.4/am/final.mdl" to "model".toByteArray(),
      "vosk-model-small-en-in-0.4/conf/model.conf" to "conf".toByteArray(),
    )
    ModelArchive.extract(ByteArrayInputStream(archive), dest)
    val root = ModelArchive.findModelRoot(dest)
    assertEquals(File(dest, "vosk-model-small-en-in-0.4").canonicalFile, root?.canonicalFile)
    assertEquals("conf", File(root, "conf/model.conf").readText())
  }

  @Test
  fun findsAModelPackedWithoutATopFolder() {
    val dest = tempDir()
    ModelArchive.extract(ByteArrayInputStream(zip("am/final.mdl" to "m".toByteArray())), dest)
    assertEquals(dest, ModelArchive.findModelRoot(dest))
    val empty = tempDir()
    assertNull(ModelArchive.findModelRoot(empty))
    assertFalse(ModelArchive.isModel(empty))
  }

  @Test
  fun rejectsEntriesOutsideTheFolder() {
    val dest = tempDir()
    val evil = zip("../evil.txt" to "x".toByteArray())
    assertThrows(IOException::class.java) { ModelArchive.extract(ByteArrayInputStream(evil), dest) }
    assertFalse(File(dest.parentFile, "evil.txt").exists())
  }

  @Test
  fun rejectsArchivesThatAreTooLarge() {
    val big = zip("a/am/final.mdl" to ByteArray(10_000))
    assertThrows(IOException::class.java) { ModelArchive.extract(ByteArrayInputStream(big), tempDir(), maxBytes = 5_000) }
    val many = zip(*Array(5) { "f$it" to ByteArray(1) })
    assertThrows(IOException::class.java) { ModelArchive.extract(ByteArrayInputStream(many), tempDir(), maxEntries = 4) }
  }

  @Test
  fun hashesWithSha256() {
    assertEquals(
      "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
      ModelArchive.sha256Hex(ByteArrayInputStream("abc".toByteArray())),
    )
    val file = File(tempDir(), "x").apply { writeText("abc") }
    assertTrue(ModelArchive.sha256Hex(file).startsWith("ba7816bf"))
  }
}
