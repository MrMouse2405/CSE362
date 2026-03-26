<script lang="ts">
    import { apiFetch } from "$lib/api";
    import { auth } from "$lib/state/auth.svelte";
    import * as Table from "$lib/components/ui/table";
    import { Badge } from "$lib/components/ui/badge";
    import { Button } from "$lib/components/ui/button";
    import * as Dialog from "$lib/components/ui/dialog";
    import * as Tabs from "$lib/components/ui/tabs";
    import * as Select from "$lib/components/ui/select";
    import * as Alert from "$lib/components/ui/alert";
    import { Separator } from "$lib/components/ui/separator";
    import { Label } from "$lib/components/ui/label";
    import { Checkbox } from "$lib/components/ui/checkbox";
    import {
        Check,
        X,
        UserCog,
        CalendarClock,
        AlertCircle,
        CheckCircle2,
    } from "@lucide/svelte";
    import { goto } from "$app/navigation";

    // ── Types ────────────────────────────────────────────────────
    interface Booking {
        id: number;
        userID: string;
        submittedByRole: string;
        roomID: number;
        status: string;
        createdAt: string;
        timeSlots: Array<{
            slot_date: string;
            start_time: string;
            end_time: string;
        }>;
    }

    interface User {
        id: string;
        email: string;
        name: string;
        role: "student" | "teacher" | "admin";
        is_active: boolean;
    }

    // ── State ────────────────────────────────────────────────────
    let pendingBookings = $state<Booking[]>([]);
    let users = $state<User[]>([]);
    let loading = $state(true);
    let error = $state("");
    let successMessage = $state("");

    // Action state
    let actionBookingId = $state<number | null>(null);
    let actionType = $state<"approve" | "deny" | null>(null);
    let dialogOpen = $state(false);

    // User Edit state
    let editingUser = $state<User | null>(null);
    let userDialogOpen = $state(false);
    let newRole = $state<string>("");
    let newActive = $state<boolean>(true);

    const roles = [
        { value: "student", label: "Student" },
        { value: "teacher", label: "Teacher" },
        { value: "admin", label: "Admin" },
    ];

    // ── Load Data ────────────────────────────────────────────────
    async function loadData() {
        loading = true;
        error = "";
        try {
            const [bookings, allUsers] = await Promise.all([
                apiFetch<Booking[]>("/api/bookings?status=pending"),
                apiFetch<User[]>("/api/auth/users"),
            ]);
            pendingBookings = bookings;
            users = allUsers;
        } catch (e) {
            error = e instanceof Error ? e.message : "Failed to load data.";
        } finally {
            loading = false;
        }
    }

    $effect(() => {
        if (!auth.isLoading && !auth.isAdmin) {
            goto("/"); // Redirect non-admin (using / as fallback for /portal)
            return;
        }
        loadData();
    });

    // ── Booking Actions ──────────────────────────────────────────
    function openConfirm(id: number, type: "approve" | "deny") {
        actionBookingId = id;
        actionType = type;
        dialogOpen = true;
    }

    async function confirmAction() {
        if (!actionBookingId || !actionType) return;

        try {
            await apiFetch(`/api/bookings/${actionBookingId}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: actionType }),
            });

            pendingBookings = pendingBookings.filter(
                (b) => b.id !== actionBookingId,
            );
            successMessage = `Booking ${actionType === "approve" ? "approved" : "denied"} successfully.`;
            setTimeout(() => (successMessage = ""), 3000);
        } catch (e) {
            error =
                e instanceof Error ? e.message : "Failed to process action.";
        } finally {
            dialogOpen = false;
            actionBookingId = null;
            actionType = null;
        }
    }

    // ── User Actions ─────────────────────────────────────────────
    function openEditUser(user: User) {
        editingUser = user;
        newRole = user.role;
        newActive = user.is_active;
        userDialogOpen = true;
    }

    async function saveUserChanges() {
        if (!editingUser) return;

        try {
            const updated = await apiFetch<User>(
                `/api/auth/users/${editingUser.id}`,
                {
                    method: "PATCH",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        role: newRole,
                        is_active: newActive,
                    }),
                },
            );

            users = users.map((u) => (u.id === updated.id ? updated : u));
            successMessage = `User ${updated.email} updated successfully.`;
            setTimeout(() => (successMessage = ""), 3000);
        } catch (e) {
            error = e instanceof Error ? e.message : "Failed to update user.";
        } finally {
            userDialogOpen = false;
            editingUser = null;
        }
    }

    function formatDate(dateStr: string) {
        return new Date(dateStr).toLocaleDateString();
    }

    function formatTime(timeStr: string) {
        return timeStr.slice(0, 5);
    }
</script>

<div class="flex flex-1 flex-col gap-6 p-6">
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-2xl font-semibold tracking-tight">
                Admin Dashboard
            </h1>
            <p class="text-muted-foreground text-sm">
                Manage booking requests and user permissions.
            </p>
        </div>
    </div>

    <Separator />

    {#if successMessage}
        <Alert.Root
            variant="default"
            class="border-green-500 bg-green-50 text-green-800"
        >
            <CheckCircle2 class="size-4" />
            <Alert.Title>Success</Alert.Title>
            <Alert.Description>{successMessage}</Alert.Description>
        </Alert.Root>
    {/if}

    {#if error}
        <Alert.Root variant="destructive">
            <AlertCircle class="size-4" />
            <Alert.Title>Error</Alert.Title>
            <Alert.Description>{error}</Alert.Description>
        </Alert.Root>
    {/if}

    <Tabs.Root value="bookings" class="w-full">
        <Tabs.List class="grid w-full max-w-[400px] grid-cols-2">
            <Tabs.Trigger value="bookings" class="flex items-center gap-2">
                <CalendarClock class="size-4" />
                Review Queue
            </Tabs.Trigger>
            <Tabs.Trigger value="users" class="flex items-center gap-2">
                <UserCog class="size-4" />
                User Management
            </Tabs.Trigger>
        </Tabs.List>

        <Tabs.Content value="bookings" class="mt-6">
            <div class="rounded-md border">
                <Table.Root>
                    <Table.Header>
                        <Table.Row>
                            <Table.Head>ID</Table.Head>
                            <Table.Head>Requester</Table.Head>
                            <Table.Head>Role</Table.Head>
                            <Table.Head>Room</Table.Head>
                            <Table.Head>Slots</Table.Head>
                            <Table.Head>Submitted</Table.Head>
                            <Table.Head class="text-right">Actions</Table.Head>
                        </Table.Row>
                    </Table.Header>
                    <Table.Body>
                        {#if loading}
                            <Table.Row>
                                <Table.Cell colspan={7} class="h-24 text-center"
                                    >Loading bookings...</Table.Cell
                                >
                            </Table.Row>
                        {:else if pendingBookings.length === 0}
                            <Table.Row>
                                <Table.Cell colspan={7} class="h-24 text-center"
                                    >No pending bookings.</Table.Cell
                                >
                            </Table.Row>
                        {:else}
                            {#each pendingBookings as booking (booking.id)}
                                <Table.Row>
                                    <Table.Cell class="font-medium"
                                        >#{booking.id}</Table.Cell
                                    >
                                    <Table.Cell
                                        >{users.find(
                                            (u) => u.id === booking.userID,
                                        )?.email || booking.userID}</Table.Cell
                                    >
                                    <Table.Cell>
                                        <Badge
                                            variant={booking.submittedByRole ===
                                            "teacher"
                                                ? "default"
                                                : "secondary"}
                                        >
                                            {booking.submittedByRole}
                                        </Badge>
                                    </Table.Cell>
                                    <Table.Cell
                                        >Room #{booking.roomID}</Table.Cell
                                    >
                                    <Table.Cell>
                                        <div class="text-xs">
                                            {#each booking.timeSlots as slot}
                                                <div>
                                                    {slot.slot_date}: {formatTime(
                                                        slot.start_time,
                                                    )}–{formatTime(
                                                        slot.end_time,
                                                    )}
                                                </div>
                                            {/each}
                                        </div>
                                    </Table.Cell>
                                    <Table.Cell
                                        >{formatDate(
                                            booking.createdAt,
                                        )}</Table.Cell
                                    >
                                    <Table.Cell class="text-right">
                                        <div class="flex justify-end gap-2">
                                            <Button
                                                size="sm"
                                                variant="outline"
                                                class="h-8 border-green-200 text-green-600 hover:bg-green-50 hover:text-green-700"
                                                onclick={() =>
                                                    openConfirm(
                                                        booking.id,
                                                        "approve",
                                                    )}
                                            >
                                                <Check class="mr-1 size-3" />
                                                Approve
                                            </Button>
                                            <Button
                                                size="sm"
                                                variant="outline"
                                                class="h-8 border-red-200 text-red-600 hover:bg-red-50 hover:text-red-700"
                                                onclick={() =>
                                                    openConfirm(
                                                        booking.id,
                                                        "deny",
                                                    )}
                                            >
                                                <X class="mr-1 size-3" />
                                                Deny
                                            </Button>
                                        </div>
                                    </Table.Cell>
                                </Table.Row>
                            {/each}
                        {/if}
                    </Table.Body>
                </Table.Root>
            </div>
        </Tabs.Content>

        <Tabs.Content value="users" class="mt-6">
            <div class="rounded-md border">
                <Table.Root>
                    <Table.Header>
                        <Table.Row>
                            <Table.Head>Name</Table.Head>
                            <Table.Head>Email</Table.Head>
                            <Table.Head>Role</Table.Head>
                            <Table.Head>Status</Table.Head>
                            <Table.Head class="text-right">Actions</Table.Head>
                        </Table.Row>
                    </Table.Header>
                    <Table.Body>
                        {#if loading}
                            <Table.Row>
                                <Table.Cell colspan={5} class="h-24 text-center"
                                    >Loading users...</Table.Cell
                                >
                            </Table.Row>
                        {:else}
                            {#each users as user (user.id)}
                                <Table.Row>
                                    <Table.Cell class="font-medium"
                                        >{user.name}</Table.Cell
                                    >
                                    <Table.Cell>{user.email}</Table.Cell>
                                    <Table.Cell>
                                        <Badge
                                            variant="outline"
                                            class="capitalize"
                                            >{user.role}</Badge
                                        >
                                    </Table.Cell>
                                    <Table.Cell>
                                        <Badge
                                            variant={user.is_active
                                                ? "default"
                                                : "destructive"}
                                        >
                                            {user.is_active
                                                ? "Active"
                                                : "Inactive"}
                                        </Badge>
                                    </Table.Cell>
                                    <Table.Cell class="text-right">
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            onclick={() => openEditUser(user)}
                                        >
                                            Edit
                                        </Button>
                                    </Table.Cell>
                                </Table.Row>
                            {/each}
                        {/if}
                    </Table.Body>
                </Table.Root>
            </div>
        </Tabs.Content>
    </Tabs.Root>
</div>

<!-- Booking Confirmation Dialog -->
<Dialog.Root bind:open={dialogOpen}>
    <Dialog.Content>
        <Dialog.Header>
            <Dialog.Title>Confirm Action</Dialog.Title>
            <Dialog.Description>
                Are you sure you want to {actionType} this booking request?
            </Dialog.Description>
        </Dialog.Header>
        <Dialog.Footer>
            <Button variant="outline" onclick={() => (dialogOpen = false)}
                >Cancel</Button
            >
            <Button
                variant={actionType === "approve" ? "default" : "destructive"}
                onclick={confirmAction}
            >
                Confirm {actionType}
            </Button>
        </Dialog.Footer>
    </Dialog.Content>
</Dialog.Root>

<!-- User Management Dialog -->
<Dialog.Root bind:open={userDialogOpen}>
    <Dialog.Content>
        <Dialog.Header>
            <Dialog.Title>Update User: {editingUser?.email}</Dialog.Title>
            <Dialog.Description>
                Modify user role and account status.
            </Dialog.Description>
        </Dialog.Header>
        <div class="grid gap-4 py-4">
            <div class="grid gap-2">
                <Label for="role">Role</Label>
                <Select.Root type="single" bind:value={newRole}>
                    <Select.Trigger class="w-full capitalize">
                        {newRole || "Select a role"}
                    </Select.Trigger>
                    <Select.Content>
                        {#each roles as role}
                            <Select.Item value={role.value} label={role.label}
                                >{role.label}</Select.Item
                            >
                        {/each}
                    </Select.Content>
                </Select.Root>
            </div>
            <div class="flex items-center gap-2">
                <input
                    type="checkbox"
                    id="is_active"
                    bind:checked={newActive}
                    class="size-4 rounded border-gray-300"
                />
                <Label for="is_active">User is active</Label>
            </div>
        </div>
        <Dialog.Footer>
            <Button variant="outline" onclick={() => (userDialogOpen = false)}
                >Cancel</Button
            >
            <Button onclick={saveUserChanges}>Save Changes</Button>
        </Dialog.Footer>
    </Dialog.Content>
</Dialog.Root>
