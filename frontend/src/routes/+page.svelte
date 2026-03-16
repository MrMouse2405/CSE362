<div class="flex flex-1 flex-col gap-4 p-4">
    <div class="grid auto-rows-min gap-4 md:grid-cols-5">
        {#each Array.from({ length: 20 }) as _, index (index)}
            <div class="bg-muted/50 aspect-square rounded-xl"></div>
        {/each}
    </div>
</div>
