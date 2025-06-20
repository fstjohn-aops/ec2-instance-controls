// If .vscode/settings.json exists, do nothing.
// If it does not exit, create it with recommended settings.

import { existsSync, writeFileSync } from "fs";

const settingsFilePath = ".vscode/settings.json";

if (existsSync(settingsFilePath)) {
  console.log(`${settingsFilePath} already exists. Skipping creation.`);
} else {
  const formatSettings = {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true,
  };

  const recommendedSettings = {
    "typescript.tsdk": "node_modules/typescript/lib",
    "typescript.enablePromptUseWorkspaceTsdk": true,
    "[typescript]": formatSettings,
    "[typescriptreact]": formatSettings,
    "[javascript]": formatSettings,
    "[javascriptreact]": formatSettings,
    "[css]": formatSettings,
    "[scss]": formatSettings,
    "[html]": formatSettings,
    "[markdown]": formatSettings,
  };

  const settingsJson = JSON.stringify(recommendedSettings, null, 2);
  const fileContent = settingsJson + "\n";

  writeFileSync(settingsFilePath, fileContent);
  console.log(`Created ${settingsFilePath} with recommended settings.`);
}
