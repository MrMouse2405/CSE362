<script lang="ts">
    let status: "idle" | "loading" | "success" | "error" = "idle";
    let message = "";
    let rawData: any = null;

    async function checkHealth() {
        status = "loading";
        try {
            // The Vite proxy routes this to http://127.0.0.1:8000 during dev.
            // In production, it hits the FastAPI backend serving the static files.
            const response = await fetch("/api/health");

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            rawData = data;
            message = data.message;
            status = "success";
        } catch (error: any) {
            console.error("Health check failed:", error);
            message = error.message;
            status = "error";
        }
    }
</script>

<div
    class="max-w-md mx-auto p-6 bg-white rounded-xl shadow-sm border border-slate-200 space-y-4"
>
    <div class="space-y-1">
        <h2 class="text-lg font-semibold tracking-tight text-slate-900">
            Backend Connection
        </h2>
        <p class="text-sm text-slate-500">
            Ping the FastAPI server to ensure the REST API is reachable.
        </p>
    </div>

    <button
        on:click={checkHealth}
        disabled={status === "loading"}
        class="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 disabled:pointer-events-none disabled:opacity-50 bg-slate-900 text-slate-50 hover:bg-slate-900/90 h-10 px-4 py-2 w-full"
    >
        {#if status === "loading"}
            Connecting...
        {:else}
            Test API Health
        {/if}
    </button>

    {#if status === "success"}
        <div
            class="p-4 bg-green-50 text-green-900 rounded-lg border border-green-200"
        >
            <div class="flex items-center space-x-2 font-medium mb-1">
                <div class="w-2 h-2 rounded-full bg-green-500"></div>
                <span>Connection Successful</span>
            </div>
            <p class="text-sm text-green-800 mb-2">{message}</p>
            <pre
                class="text-xs bg-green-100/50 p-2 rounded border border-green-200/50 overflow-x-auto"><code
                    >{JSON.stringify(rawData, null, 2)}</code
                ></pre>
        </div>
    {:else if status === "error"}
        <div
            class="p-4 bg-red-50 text-red-900 rounded-lg border border-red-200"
        >
            <div class="flex items-center space-x-2 font-medium mb-1">
                <div class="w-2 h-2 rounded-full bg-red-500"></div>
                <span>Connection Failed</span>
            </div>
            <p class="text-sm text-red-800">{message}</p>
        </div>
    {/if}
</div>
