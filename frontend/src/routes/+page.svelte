<script lang="ts">
    import { onMount } from "svelte";
    import Button from "$lib/components/ui/button/button.svelte";

    let value = 0;

    // Define the shape of your API response for TypeScript
    interface ApiResponse {
        number: number;
    }

    async function get() {
        try {
            const response = await fetch("/api/numbers/rand");
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data: ApiResponse = await response.json();
            value = data.number;
        } catch (error) {
            console.error("Fetch failed:", error);
            value = -1;
        }
    }

    onMount(async () => {
        await get();
    });
</script>

<p>Server Replied: {value}</p>

<Button onclick={get}>new number</Button>
