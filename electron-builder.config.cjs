// @ts-check

/** @type {import('electron-builder').Configuration} */
module.exports = {
  appId: "com.speakeasy.desktop",
  productName: "SpeakEasy",
  directories: {
    buildResources: "build",
  },
  files: [
    "!**/.vscode/*",
    "!src/*",
    "!scripts/*",
    "!electron.vite.config.{js,ts,mjs,cjs}",
    "!{.eslintignore,.eslintrc.cjs,.prettierignore,.prettierrc.yaml,dev-app-update.yml,CHANGELOG.md,README.md}",
    "!{.env,.env.*,.npmrc,pnpm-lock.yaml}",
    "!{tsconfig.json,tsconfig.node.json,tsconfig.web.json}",
    "!*.{js,cjs,mjs,ts}",
    "!components.json",
    "!.prettierrc",
    '!speakeasy-rs/*'
  ],
  asarUnpack: ["resources/**", "node_modules/**"],
  extraResources: [
    {
      from: "speakeasy-rs/target/release/speakeasy-rs.exe",
      to: "bin/speakeasy-rs.exe"
    },
    {
      from: "../speakeasy-core/dist/speakeasy-core",
      to: "bin/speakeasy-core"
    }
  ],
  win: {
    executableName: "speakeasy",
    // Desabilita assinatura de código para builds locais
    signAndEditExecutable: false,
  },
  nsis: {
    artifactName: "SpeakEasy-${version}-${arch}.${ext}",
    shortcutName: "${productName}",
    uninstallDisplayName: "${productName}",
    createDesktopShortcut: "always",
  },
  mac: {
    binaries: [`resources/bin/speakeasy-rs${process.platform === 'darwin' ? '' : '.exe'}`],
    artifactName: "${productName}-${version}-${arch}.${ext}",
    entitlementsInherit: "build/entitlements.mac.plist",
    extendInfo: [
      {
        NSCameraUsageDescription:
          "Application requests access to the device's camera.",
      },
      {
        NSMicrophoneUsageDescription:
          "Application requests access to the device's microphone.",
      },
      {
        NSDocumentsFolderUsageDescription:
          "Application requests access to the user's Documents folder.",
      },
      {
        NSDownloadsFolderUsageDescription:
          "Application requests access to the user's Downloads folder.",
      },
    ],
    notarize: process.env.APPLE_TEAM_ID
      ? {
        teamId: process.env.APPLE_TEAM_ID,
      }
      : undefined,
  },
  dmg: {
    artifactName: "${productName}-${version}-${arch}.${ext}",
  },
  linux: {
    target: ["AppImage", "snap", "deb"],
    maintainer: "electronjs.org",
    category: "Utility",
  },
  appImage: {
    artifactName: "${name}-${version}.${ext}",
  },
  npmRebuild: false,
  publish: {
    provider: "github",
    owner: "egoist",
    repo: "speakeasy",
  },
  removePackageScripts: true,
}
