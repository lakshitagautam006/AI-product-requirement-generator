# Product Requirement Document (PRD) Industry Standards & Best Practices

## Purpose of a PRD
A Product Requirement Document (PRD) is a foundational guide that outlines what a product should do, why it is being built, who it is for, and how success will be measured. It bridges business strategy, user needs, and engineering execution.

## Core Components of an Industry-Standard PRD

### 1. Problem Statement & Context
- **The Core Problem**: A clear, concise statement describing the pain point or unmet need.
- **Target Audience / Impact**: Who experiences this problem and what is the negative impact (loss of time, money, productivity)?
- **Current Alternatives & Limitations**: How do users currently cope, and why are existing solutions inadequate?
- **Proposed Solution & Value Proposition**: High-level pitch of the product and its unique differentiator.

### 2. User Personas
Each persona must represent a primary user archetype:
- **Demographics & Role**: Name, job/student status, environment.
- **Goals & Motivations**: What are they trying to accomplish?
- **Frustrations & Pain Points**: What blocks them today?
- **Technical Savviness**: How comfortable are they with digital tools?
- **User Quote / Mindset**: A one-liner expressing their key perspective.

### 3. User Stories (INVEST Framework)
User stories should follow the standard Agile format:
- **Format**: `As a <type of user>, I want to <perform an action>, so that <achieve a business or personal outcome>.`
- **Acceptance Criteria**: Defined using `Given [precondition], When [action], Then [expected outcome]`.
- **INVEST Principle**: Stories should be Independent, Negotiable, Valuable, Estimable, Small, and Testable.

### 4. Functional Requirements
Functional requirements define specific behaviors and capabilities of the system.
- Organized by feature domain or module (e.g., Authentication, Core Workflow, Notifications, Reporting).
- Prioritized using MoSCoW methodology:
  - **Must-Have (P0)**: Core essential MVP features.
  - **Should-Have (P1)**: Important enhancements for major launch.
  - **Nice-to-Have (P2)**: Future roadmap considerations.
- Every requirement must have a unique ID (e.g., `FR-001`), description, input/output behavior, and priority level.
