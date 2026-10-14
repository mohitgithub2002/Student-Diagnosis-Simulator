// The shared task library lives outside this app (packages/task-library); let Metro watch and resolve it.
const path = require("path");
const { getDefaultConfig } = require("expo/metro-config");

const projectRoot = __dirname;
const monorepoRoot = path.resolve(projectRoot, "../..");
const config = getDefaultConfig(projectRoot);
config.watchFolders = [path.join(monorepoRoot, "packages", "task-library")];
config.resolver.nodeModulesPaths = [path.join(projectRoot, "node_modules")];
config.resolver.unstable_enableSymlinks = true;
module.exports = config;
