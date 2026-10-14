const { AndroidConfig, withAndroidManifest } = require("expo/config-plugins");

/**
 * Release builds block plain http:// by default. Allow it only when the configured API or model server is
 * http (the emulator or a local pilot server); production should use https and then this plugin is unused.
 */
module.exports = function withCleartextTraffic(config) {
  return withAndroidManifest(config, (c) => {
    AndroidConfig.Manifest.getMainApplicationOrThrow(c.modResults).$["android:usesCleartextTraffic"] = "true";
    return c;
  });
};
