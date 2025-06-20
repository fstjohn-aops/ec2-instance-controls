# `fastack-starter`

> [!TIP]
> For Hackathon projects, you might find it easier to use [create-next-app](https://nextjs.org/docs/app/api-reference/cli/create-next-app) for rapid startup, then migrate to Fastack later if needed. You can also [copy this prompt into Cursor agent](https://docs.google.com/document/d/1tze8w0sTGvzVTOwZRDvHNMzYi2PHuv_0ewaish29Ook/edit?tab=t.0#heading=h.8rsthp7ixegq) to set up a new Next.js project.
>
> Otherwise, Fastack does offer some conveniences like:
>
> - Platform integration
> - Postgres and Redis databases
> - Docker configurations suitable for local development
> - Default ESLint, Prettier, Jest, TypeScript, VS Code configurations

> [!WARNING]
> During Hackathon, to run your project on an AWS EC2 instance, it will need Docker and Node.js installed.
>
> It will also need either `trove`, or an AWS CLI profile with credentials to login to AWS CodeArtifact (nearly identical to [installing trove packages in Docker](https://github.com/aops-ba/trove?tab=readme-ov-file#in-docker)).
>
> Then, you will need to clone, configure, and run your project as if it was development.
>
> Running in a screen session is recommended:
>
> ```bash
> screen
> npm run dev
> ```

## 🚀 Create a New Fastack Project

This monorepo is a [**template repo**](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template) for creating a new "Fastack" project, featuring:

- **Fastify backend** for:
  - API endpoints
  - Business logic
  - Reading/writing data
  - Integrating with 3rd party APIs
- **Next.js frontend** for:
  - Serving the UI
  - Managing Platform sessions
- **PostgreSQL database** for:
  - Application data
- **Redis database** for:
  - Performant caching
- **Additional tools:**
  - Generators for TypeScript types + TypeBox validators
  - Jest for automated unit testing
  - ESLint for linting
  - Prettier for formatting

---

## 📑 Table of Contents

- [How To Use This Template](#-how-to-use-this-template)
  - [1. Install Requirements](#1-install-requirements)
  - [2. Create New Repo](#2-create-new-repo)
  - [3. Clone New Repo Locally](#3-clone-new-repo-locally)
  - [4. Install Dependencies](#4-install-dependencies)
  - [5. Configure Environment Variables](#5-configure-environment-variables)
  - [6. Setup the Database](#6-setup-the-database)
  - [7. Run Project in Dev Mode](#7-run-project-in-dev-mode)
- [Repository Structure](#-repository-structure)
- [Give Feedback](#-give-feedback)
- [Feature Roadmap](#-feature-roadmap)

---

## 📦 How To Use This Template

### 1. Install Requirements

1. [Install fnm](https://github.com/Schniz/fnm?tab=readme-ov-file#using-a-script-macoslinux) (recommended)

- This will allow you to install and switch between different Node versions. This project uses Node.js 22.

- Alternatives:
  - [nvm](https://github.com/nvm-sh/nvm)
  - [Install Node.js directly](https://nodejs.org/en/download/package-manager)

2. [Install Docker Desktop](https://www.docker.com/products/docker-desktop/)

- You will need this to run PostgreSQL and Redis locally.

3. [Install Trove CLI](https://github.com/aops-ba/trove#installation)

- This will allow you to install and use the private NPM registry for the required `@aops-trove/*` Node.js packages.

### 2. Create New Repo

1. From Github, click the **"Use this template"** button at the top of the page.
2. Click **"Create a new repository"**.
3. Name your repo whatever you want.

https://github.com/aops-ba/fastack-starter/assets/15165138/be950c04-20e0-4d24-b278-d366381ca3a2

### 3. Clone New Repo Locally

1. From your new repo, click the **"Code"** button and copy the URL.
2. Clone the repo with your terminal.

   ```bash
   cd ~ # Navigate to your home directory.
   git clone <repo-url> # Clone the repo.
   ```

### 4. Install Dependencies

1. Navigate to the root of your new repo.

   ```bash
   cd ~/<repo-name> # Navigate to the root of the project.
   ```

2. Install dependencies.

   ```bash
   fnm use # Use the project's Node version.
   npm install # Install dependencies.
   ```

### 4. Run the Dev Setup Script

1. Run the following command to setup the development environment. Follow the instructions in the terminal to complete setup.

   ```bash
   npm run dev-setup
   ```

![image](https://github.com/user-attachments/assets/478b39cc-3031-4685-8192-3363888504b7)

### 5. Run Project in Dev Mode

1. Run the following command to simultaneously start Fastify, Next.js, PostgreSQL, and Redis in dev mode.

   ```bash
   npm run dev
   ```

2. Open http://localhost:13030/ in your browser.

---

## 📂 Repository Structure

| Folder   | Framework | Purpose                                                                                              |
| -------- | --------- | ---------------------------------------------------------------------------------------------------- |
| `server` | Fastify   | A Fastify server for managing backend business logic, API endpoints, and database queries.           |
| `nextjs` | Next.js   | A Next.js App Router frontend for serving the UI and handling Platform sessions.                     |
| `types`  | n/a       | Tooling for generating TypeScript types and TypeBox validators shared between `server` and `nextjs`. |

---

## 📣 Give Feedback

Have an idea, need help, or want to share feedback? Start a thread in [\#eng-swa](https://join.slack.com/share/enQtNjkwODA2NjQ1MDY1Ni04NTYyMmQwNzk5YjVhMGU1YmE2MmRhYzI2NThiODQwMGNjNmY3MWE4ZjMwZGNhMjg1MDg4ZmFhOTY2NjVlZjg1).

---

## 🚧 Feature Roadmap

- [ ] **Dependency Updates**

  - [ ] Update Next.js to 15.

- [ ] **Production-ready Docker Config**

  - [ ] Make sure Docker configurations are cleaned up and production-ready.

- [ ] **Fast Dev Setup**

  - [ ] "1-button workflow" for creating and running a new Fastack project from this template.

- [ ] **Streamline Future Maintenance and Development**

  - [ ] Move core application code into [trove-shared](https://github.com/aops-ba/trove-shared) packages instead of as standalone files in this repo that get copied.

- [ ] **Improve Performance**

  - [ ] Force static rendering of Next.js pages by default.
  - [ ] Remove usage of dynamic APIs in core application code.

- [ ] **Improve DX**

  - [ ] Default CodeCov integration (potentially in a monorepo).
  - [ ] Default Github Actions CI workflow (potentially in a monorepo).
  - [ ] Default DataDog APM integration.
  - [ ] Streamline Platform API usage.

- [ ] **Improve Documentation**

  - [ ] More thorough documentation on valuable patterns and practices.
  - [ ] Default docgen implementation for API endpoints.
