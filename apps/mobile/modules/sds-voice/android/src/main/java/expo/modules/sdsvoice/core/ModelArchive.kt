package expo.modules.sdsvoice.core

import java.io.File
import java.io.IOException
import java.io.InputStream
import java.security.MessageDigest
import java.util.zip.ZipInputStream

/** Unpacking and checking downloaded speech model archives. No Android classes, so it runs in JVM unit tests. */
object ModelArchive {
  const val MAX_BYTES = 400L * 1024 * 1024
  const val MAX_ENTRIES = 5_000

  /**
   * Extracts a zip into [dest]. Entries that would land outside [dest] are rejected, as are archives
   * that unpack to more than [maxBytes] or hold more than [maxEntries] entries.
   */
  fun extract(zip: InputStream, dest: File, maxBytes: Long = MAX_BYTES, maxEntries: Int = MAX_ENTRIES) {
    val root = dest.canonicalFile
    if (!root.isDirectory && !root.mkdirs()) throw IOException("Cannot create $root")
    var total = 0L
    var entries = 0
    val buffer = ByteArray(64 * 1024)
    ZipInputStream(zip.buffered()).use { zin ->
      while (true) {
        val entry = zin.nextEntry ?: break
        if (++entries > maxEntries) throw IOException("Archive has too many entries")
        val target = File(root, entry.name).canonicalFile
        if (!target.path.startsWith(root.path + File.separator)) throw IOException("Unsafe entry ${entry.name}")
        if (entry.isDirectory) {
          target.mkdirs()
          continue
        }
        target.parentFile?.mkdirs()
        target.outputStream().use { out ->
          while (true) {
            val n = zin.read(buffer)
            if (n < 0) break
            total += n
            if (total > maxBytes) throw IOException("Archive is too large")
            out.write(buffer, 0, n)
          }
        }
      }
    }
  }

  /**
   * The folder holding the model (the one with am/final.mdl): [dir] itself, or its only subfolder, which is
   * how the official archives are packed ("vosk-model-small-en-in-0.4/am/final.mdl").
   */
  fun findModelRoot(dir: File): File? {
    if (isModel(dir)) return dir
    val children = dir.listFiles()?.filter { !it.name.startsWith(".") } ?: return null
    val only = children.singleOrNull() ?: return null
    return if (only.isDirectory && isModel(only)) only else null
  }

  fun isModel(dir: File): Boolean = File(dir, "am/final.mdl").isFile

  fun sha256Hex(input: InputStream): String {
    val md = MessageDigest.getInstance("SHA-256")
    val buf = ByteArray(64 * 1024)
    while (true) {
      val n = input.read(buf)
      if (n < 0) break
      md.update(buf, 0, n)
    }
    return md.digest().joinToString("") { "%02x".format(it) }
  }

  fun sha256Hex(file: File): String = file.inputStream().use { sha256Hex(it) }
}
