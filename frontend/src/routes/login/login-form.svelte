<script lang="ts">
    import { goto } from "$app/navigation";
    import { Button } from "$lib/components/ui/button/index.js";
    import * as Card from "$lib/components/ui/card/index.js";
    import { Input } from "$lib/components/ui/input/index.js";
    import {
        FieldGroup,
        Field,
        FieldLabel,
        FieldDescription,
    } from "$lib/components/ui/field/index.js";
    import { auth } from "$lib/state/auth.svelte";

    const id = $props.id();
    let email = $state("");
    let password = $state("");
    let error = $state("");
    let loading = $state(false);

    async function handleSubmit(e: Event) {
        e.preventDefault();
        error = "";
        loading = true;

        try {
            await auth.login(email, password);
            goto("/");
        } catch (err) {
            error = err instanceof Error ? err.message : "Login failed";
        } finally {
            loading = false;
        }
    }
</script>

<Card.Root class="mx-auto w-full max-w-sm">
    <Card.Header>
        <Card.Title class="text-2xl">Login</Card.Title>
        <Card.Description
            >Enter your email below to login to your account</Card.Description
        >
    </Card.Header>
    <Card.Content>
        <form onsubmit={handleSubmit}>
            <FieldGroup>
                <Field>
                    <FieldLabel for="email-{id}">Email</FieldLabel>
                    <Input
                        id="email-{id}"
                        type="email"
                        placeholder="m@example.com"
                        required
                        bind:value={email}
                    />
                </Field>
                <Field>
                    <FieldLabel for="password-{id}">Password</FieldLabel>
                    <Input id="password-{id}" type="password" required bind:value={password} />
                </Field>
                {#if error}
                    <p class="text-sm text-red-500">{error}</p>
                {/if}
                <Field>
                    <Button type="submit" class="w-full" disabled={loading}>
                        {loading ? "Logging in..." : "Login"}
                    </Button>
                    <FieldDescription class="text-center">
                        Don't have an account? <a href="/register" class="underline">Sign up</a>
                    </FieldDescription>
                </Field>
            </FieldGroup>
        </form>
    </Card.Content>
</Card.Root>
