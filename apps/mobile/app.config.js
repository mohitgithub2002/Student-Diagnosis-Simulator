/**
 * Server addresses can be set at build time: SDS_API_URL (the FastAPI backend) and SDS_MODELS_URL (where the
 * web app serves /models/ with the speech models). The defaults suit the Android emulator on a dev machine.
 */
module.exports = ({ config }) => {
  const apiUrl = process.env.SDS_API_URL ?? config.extra?.apiUrl ?? "http://10.0.2.2:8000";
  const modelsUrl = process.env.SDS_MODELS_URL ?? config.extra?.modelsUrl ?? "http://10.0.2.2:5173/models";
  const cleartext = [apiUrl, modelsUrl].some((u) => u.startsWith("http:"));
  return {
    ...config,
    extra: { ...config.extra, apiUrl, modelsUrl },
    plugins: [...(config.plugins ?? []), ...(cleartext ? ["./plugins/withCleartextTraffic"] : [])],
  };
};
