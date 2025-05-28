const express = require("express");
const axios = require("axios");
const cheerio = require("cheerio");
const AdmZip = require("adm-zip");
const os = require("os");

const app = express();
const PORT = 15608;

const MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json";

let cachedManifest = null;

// Fetch and cache manifest
async function loadManifest() {
  if (!cachedManifest) {
    const { data } = await axios.get(MANIFEST_URL);
    cachedManifest = data.versions;
  }
  return cachedManifest;
}

// Function to scrape the Minecraft Wiki for version info
async function getMinecraftWikiInfo(versionId) {
  try {
    const wikiUrl = `https://minecraft.wiki/w/Java_Edition_${versionId}`;
    const { data } = await axios.get(wikiUrl);
    const $ = cheerio.load(data);

    let title = "";
    let resourcePackVersion = null;

    // Find the title (Official name or Snapshot)
    const titleRow = $("th:contains('Official name'), th:contains('Snapshot')").closest("tr");
    if (titleRow.length) {
      title = titleRow.find("td").text().replace(/\n/g, "").trim();
    }

    // Find the Resource Pack format
    const resourceRow = $("th:contains('Resource pack format')").closest("tr");
    if (resourceRow.length) {
      resourcePackVersion = resourceRow.find("td p").text().trim();
    }

    return { title, resourcePackVersion };
  } catch (error) {
    console.error("Error scraping Minecraft Wiki:", error.message);
    return { title: "Unknown", resourcePackVersion: null };
  }
}

// Endpoint to list all version IDs
app.get("/versions", async (req, res) => {
  try {
    const versions = await loadManifest();
    const versionIds = versions.map(v => v.id);
    res.json(versionIds);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Endpoint to get detailed info about a specific version
app.get("/version/:versionId", async (req, res) => {
  try {
    const { versionId } = req.params;
    const versions = await loadManifest();
    const version = versions.find(v => v.id === versionId);

    if (!version) {
      return res.status(404).json({ error: "Version not found" });
    }

    const { data: versionMeta } = await axios.get(version.url);

    // Correct Java version: show only the major number like 21, 17, etc
    const javaVersion = versionMeta.javaVersion
      ? String(versionMeta.javaVersion.majorVersion || "unknown")
      : "unknown";

    const clientJarUrl = versionMeta.downloads?.client?.url;
    if (!clientJarUrl) {
      return res.status(404).json({ error: "Client JAR not available" });
    }

    const clientJar = await axios.get(clientJarUrl, { responseType: "arraybuffer" });
    const zip = new AdmZip(clientJar.data);
    const entry = zip.getEntries().find(e => e.entryName.endsWith("pack.mcmeta"));

    let datapackVersion = null;

    if (entry) {
      const packMeta = JSON.parse(entry.getData().toString("utf8"));
      datapackVersion = packMeta.pack?.pack_format ?? null;
    }

    const minecraftWikiInfo = await getMinecraftWikiInfo(versionId);

    res.json({
      id: version.id,
      type: version.type,
      java_version: javaVersion,
      datapack_version: datapackVersion,
      resource_pack_version: minecraftWikiInfo.resourcePackVersion || "Not available",
      update_title: minecraftWikiInfo.title || "No update title available",
      release_time: versionMeta.releaseTime,
      release_time_formatted: new Date(versionMeta.releaseTime).toLocaleString(),
      client_url: clientJarUrl,
      server_url: versionMeta.downloads?.server?.url || "Server jar not available",
      wikiurl: `https://minecraft.wiki/w/Java_Edition_${version.id}`
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get local IP address
const getLocalIP = () => {
  const networkInterfaces = os.networkInterfaces();
  for (let interfaceName in networkInterfaces) {
    for (let interfaceInfo of networkInterfaces[interfaceName]) {
      if (interfaceInfo.family === 'IPv4' && !interfaceInfo.internal) {
        return interfaceInfo.address;
      }
    }
  }
  return 'localhost';
};

// Start the server with local IP address
app.listen(PORT, () => {
  const localIP = getLocalIP();
  console.log(`Minecraft API server running at http://${localIP}:${PORT}/`);
});
