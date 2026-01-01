import { child_process, spawn } from "child_process"
import path from "path"
import { app } from "electron"

export class PythonBridge {
    private static process: any = null

    static start() {
        if (this.process) return

        const pythonPath = "python" // Should be configurable or venv path
        const scriptPath = path.join(app.getAppPath(), "..", "juris-transcritor-python", "main.py")

        console.log(`[PythonBridge] Starting daemon: ${scriptPath}`)

        this.process = spawn(pythonPath, [scriptPath], {
            stdio: "inherit",
            windowsHide: true
        })

        this.process.on("error", (err) => {
            console.error("[PythonBridge] Failed to start python process:", err)
        })

        app.on("quit", () => {
            this.stop()
        })
    }

    static stop() {
        if (this.process) {
            console.log("[PythonBridge] Stopping daemon...")
            this.process.kill()
            this.process = null
        }
    }
}
