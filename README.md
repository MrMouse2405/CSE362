# CSE362 Lab 2

## Dependencies

`uv` package manager for python (fastapi) backend

`bun` package manager for javascript (sveltekit+typescript) frontend. 

`bun` is not required if you are not debugging the frontend. Frontend
html should already be generated and added to version control.
if not, see [Building Front End](#building-the-front-end)

## Running

Set the following environment variables in .env

**NOTE:** Use a cryptographically secure random string for the SECRET_KEY.

```env
ROOT_USER_NAME=root
ROOT_USER_PASSWORD=your_root_password_here
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:///database.db
```

HTML should already be generated and added to version control.
if not, see [Building Front End](#building-the-front-end)

### Running the FastAPI server:

```bash
cd backend
uv run fastapi run
```

### Debugging / developing the backend

```bash
cd backend
uv run fastapi dev
```

## Building the front end

You will need to build the front end using the following command:

```bash
cd frontend
bun install # once to install dependencies
bun run build # to generate static html content
```

### Debugging/developing the front end

You will also need to run the backend using:

```bash
cd backend
uv run fastapi run # or uv run fastapi dev
```
Then you may run the frontend using:

```bash
cd frontend
bun run dev
```

The front end uses vite proxy to connect to the backend.

So feel free to make requests to backend using relative paths:

```js
fetch("/api/v0/example/rand")
```
