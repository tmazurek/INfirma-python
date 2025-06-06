Okay, I understand. Tailwind CSS, while powerful, can have a learning curve and a specific workflow that doesn't suit everyone or every project initially. Switching to Vue.js's default styling approaches (scoped CSS or CSS Modules) is perfectly fine and often simpler to get started with.

We'll rewrite **Phase 2: Frontend UI Development using Vue.js**, removing Tailwind CSS and relying on Vue's built-in styling mechanisms. This will mean more traditional CSS/SCSS writing within components.

**Primary Guiding Models for Vue.js Frontend Development (Default Styling):**

1.  **Jobs-to-be-Done (JTBD):** The Vue.js frontend must provide an intuitive, efficient, and visually clear interface for the Polish accounting application, enabling users to manage their finances effortlessly by interacting with the FastAPI backend.
2.  **Nielsen's Usability Heuristics & Cognitive Load:** These remain paramount for UI/UX design.
3.  **Component-Based Architecture (Vue):** Vue's component system will be used for modular UI.
4.  **Single Page Application (SPA) Experience:** A smooth, responsive SPA.
5.  **Scoped CSS / CSS Modules (Vue):** Leverage Vue's features for component-specific styling to avoid global style conflicts and improve maintainability.

**Confidence Score:** High (that Vue.js with its default styling mechanisms can effectively create the required UI).

**Key Assumptions (Vue.js Frontend Context - Default Styling):**

1.  **Backend API Stability:** The FastAPI backend (Phase 1) is complete and operational.
2.  **SPA Architecture:** Frontend as a Single Page Application.
3.  **Modern JavaScript Ecosystem:** Node.js, npm/yarn, Vite (or Vue CLI).
4.  **Styling:** **Scoped CSS (`<style scoped>`) or CSS Modules within Vue components.** This means writing standard CSS or a preprocessor like SCSS directly in your `.vue` files. We will *not* use a utility-first framework like Tailwind.
5.  **State Management:** Pinia (or Vuex / Vue's reactivity).
6.  **Routing:** Vue Router.

---

<MARKDOWN_DOCUMENT title="Polish Accounting App - Phase 2: Vue.js Frontend UI Development Blueprint (Default Styling)">

## Polish Accounting App - Phase 2: Vue.js Frontend UI Development Blueprint (Default Styling)

This document outlines the blueprint for **Phase 2: Frontend User Interface (UI) Development** of the Polish accounting application, using Vue.js (preferably Vue 3) and its default styling mechanisms (Scoped CSS or CSS Modules). It assumes the FastAPI backend API (Phase 1) is complete and operational.

**I. High-Level Architecture & Technology Stack (Frontend - Phase 2):**

*   **Framework:** Vue.js (Version 3 recommended).
*   **Build Tool:** Vite (recommended for Vue 3) or Vue CLI.
*   **Routing:** Vue Router for client-side navigation.
*   **State Management (Consider based on complexity):**
    *   Vue's built-in reactivity system.
    *   Pinia (official, lightweight state management for Vue 3).
*   **Styling:**
    *   **Scoped CSS (`<style scoped>`):** Styles defined within a `.vue` file's `<style scoped>` tag will only apply to elements of that component. This is the most common approach in Vue for component-level styling.
    *   **CSS Modules:** Another option where CSS class names are locally scoped by default.
    *   **Global Styles:** A global CSS file (e.g., `src/assets/main.css`) can be used for base styles, resets, and overall application theme variables (CSS custom properties).
    *   **CSS Preprocessors (Optional):** SCSS/Sass can be integrated if more advanced CSS features are desired.
*   **API Communication:**
    *   Axios or the native `fetch` API for asynchronous requests to the FastAPI backend.
*   **UI Components:** Custom Vue components for reusable UI elements. Each component will have its own scoped styles.
*   **Deployment:** Static site hosting or served by a simple web server.

**II. Core Frontend Modules, Views (Routes), and Components:**

Each module will consist of Vue views and sub-components. Styling will be handled primarily via scoped CSS within each `.vue` file. Global styles will define the base look and feel.

**1. Global UI Structure & Core Components:**
    *   **JTBD:** "Provide a consistent, intuitive, and responsive application shell for easy navigation and interaction."
    *   **Main App Layout (`App.vue`):**
        *   Contains the primary structure: Header/Navigation, main content area (`<router-view>`), Footer.
        *   Will import global styles (e.g., `import '@/assets/main.css';`).
    *   **Navigation Component (`components/layout/TheNavigation.vue`):**
        *   Responsive navigation bar. Styled with its own scoped CSS.
        *   Links to main sections.
    *   **Reusable UI Components (`components/ui/`):**
        *   `BaseButton.vue`, `BaseInput.vue`, `BaseSelect.vue`, `BaseModal.vue`, `BaseTable.vue`, `BaseCard.vue`, `LoadingSpinner.vue`, `ErrorMessage.vue`.
        *   Each will have its own `<style scoped>` section for appearance and layout. They will be designed to be themable via props or CSS custom properties if needed.
    *   **Dashboard View (`views/DashboardView.vue` - Route: `/`):**
        *   Landing page. Displays key summary figures. Quick links. Styled with its own scoped CSS.

**2. Company Profile & Settings Module:**
    *   **JTBD:** "Enable easy viewing and management of company details, tax, and ZUS settings through clear forms."
    *   **Views (Routed Components):**
        *   `views/settings/CompanyProfileView.vue`
        *   `views/settings/TaxSettingsView.vue`
        *   `views/settings/ZusSettingsView.vue`
    *   **Components (`components/settings/`):**
        *   `CompanyProfileForm.vue`, `TaxSettingsForm.vue`, `ZusSettingsForm.vue`.
        *   Each form will have its inputs, labels, and layout styled via its scoped CSS. Tooltips or help text can be implemented with simple HTML elements and styled.
    *   **State Management (Pinia Store - e.g., `stores/settingsStore.js`):** Manages fetching/updating settings, loading/error states.
    *   **Usability:** Forms will use standard HTML5 validation attributes, supplemented by client-side Vue validation (e.g., custom logic or a library like Vuelidate/VeeValidate if complex validation is needed beyond HTML5).

**3. Client Management Module:**
    *   **JTBD:** "Provide an efficient interface to add, find, view, and update client information."
    *   **Views (Routed Components):**
        *   `views/clients/ClientListView.vue`
        *   `views/clients/ClientCreateView.vue`
        *   `views/clients/ClientEditView.vue`
        *   `views/clients/ClientDetailView.vue`
    *   **Components (`components/clients/`):**
        *   `ClientTable.vue` or `ClientCard.vue` (styled with scoped CSS for table rows, cells, card layout).
        *   `ClientForm.vue`.
    *   **State Management (Pinia Store - e.g., `stores/clientStore.js`).**

**4. Invoice Management Module:**
    *   **JTBD:** "Offer an intuitive system to create professional invoices, manage them, track status, and download PDFs."
    *   **Views (Routed Components):**
        *   `views/invoices/InvoiceListView.vue`
        *   `views/invoices/InvoiceCreateView.vue`
        *   `views/invoices/InvoiceEditView.vue`
        *   `views/invoices/InvoiceDetailView.vue`
    *   **Components (`components/invoices/`):**
        *   `InvoiceTable.vue` or `InvoiceCard.vue`.
        *   `InvoiceForm.vue`: A complex component.
            *   Client selection (e.g., a styled `<select>` or a custom searchable dropdown component).
            *   Date pickers (could be styled native HTML5 date inputs, or a lightweight Vue date picker component if one is chosen, which would bring its own styling).
            *   Dynamic Line Item Management: `InvoiceItemFormRow.vue` components, each with its own scoped styles for inputs and layout within the row.
        *   `InvoiceItemFormRow.vue`.
    *   **State Management (Pinia Store - e.g., `stores/invoiceStore.js`).**
    *   **Styling Note:** The invoice form will require careful CSS to ensure a clean, usable layout, especially for the dynamic line items. Flexbox or CSS Grid within scoped styles will be heavily used.

**5. Expense Tracking Module:**
    *   **JTBD:** "Allow quick logging and review of business expenses."
    *   **Views (Routed Components):**
        *   `views/expenses/ExpenseListView.vue`
        *   `views/expenses/ExpenseCreateView.vue`
        *   `views/expenses/ExpenseEditView.vue`
    *   **Components (`components/expenses/`):**
        *   `ExpenseTable.vue` or `ExpenseCard.vue`.
        *   `ExpenseForm.vue`.
    *   **State Management (Pinia Store - e.g., `stores/expenseStore.js`).**

**6. Financial Reporting Module:**
    *   **JTBD:** "Present my monthly financial summary and estimated tax/ZUS liabilities clearly."
    *   **Views (Routed Components):**
        *   `views/reports/MonthlySummaryView.vue`:
            *   Month/year selector component.
            *   Fetched data displayed in well-structured sections, styled using scoped CSS for cards, tables, or typographic hierarchy.
            *   **Crucial:** Highly visible disclaimer about estimates, styled for prominence.
    *   **Components (`components/reports/`):**
        *   `MonthYearSelector.vue`.
        *   Components for displaying summary sections (e.g., `VatSummaryDisplay.vue`, `ZusBreakdownDisplay.vue`), each with their own scoped styles.
    *   **State Management (Pinia Store - e.g., `stores/reportStore.js`).**

**III. Key Development Tasks (Frontend UI - Vue.js - Default Styling):**

*(Commit frequently. Each component will involve writing HTML template, JavaScript logic, and CSS within its `<style scoped>` block.)*

1.  **Task VUE_DS_F01:** Project Setup: 
    *   Initialize Vue 3 project (Vite).
    *   Install Vue Router, Pinia (if chosen), Axios (if chosen).
    *   Create `src/assets/main.css` for global styles (reset, base typography, common variables).
    *   Basic `App.vue` layout, router setup with placeholder routes.
2.  **Task VUE_DS_F02:** Global UI Components & Dashboard Shell:
    *   Develop `TheNavigation.vue`, basic `DashboardView.vue`. Style them using scoped CSS.
    *   Create initial `Base*.vue` UI components (Button, Input, Card). Style them with flexible, reusable scoped CSS.
3.  **Task VUE_DS_F03:** Company Profile & Settings UI:
    *   Develop views and forms. Style all elements (labels, inputs, sections, help text) with scoped CSS.
    *   Implement API interactions and state management.
4.  **Task VUE_DS_F04:** Client Management UI:
    *   Develop views and forms. Style tables, cards, forms with scoped CSS.
    *   API/state management.
5.  **Task VUE_DS_F05:** Expense Tracking UI:
    *   Develop views and forms with scoped CSS. API/state management.
6.  **Task VUE_DS_F06:** Invoice Management UI - Listing & Viewing:
    *   Develop `InvoiceListView.vue`, `InvoiceDetailView.vue`. Style lists/details. PDF download.
7.  **Task VUE_DS_F07:** Invoice Management UI - New/Edit Invoice Form (`InvoiceForm.vue`):
    *   Major task. Focus on clean layout for the form and dynamic line items using scoped CSS (Flexbox/Grid). Real-time calculations.
8.  **Task VUE_DS_F08:** Invoice Management UI - Actions: Wire up buttons, update UI state.
9.  **Task VUE_DS_F09:** Financial Reporting UI - Monthly Summary:
    *   Develop `MonthlySummaryView.vue`. Style data presentation clearly using scoped CSS.
10. **Task VUE_DS_F10:** Populate Dashboard: Fetch and display metrics.
11. **Task VUE_DS_F11:** Global Error Handling & Notifications: Style notification components.
12. **Task VUE_DS_F12:** Loading States: Style loading indicators.
13. **Task VUE_DS_F13:** Responsive Design with CSS: Use media queries within scoped CSS (or in global CSS for layout breakpoints) to ensure responsiveness. Test thoroughly.
14. **Task VUE_DS_F14:** Usability Review & Iteration.
15. **Task VUE_DS_F15:** Accessibility (A11y) Review.
16. **Task VUE_DS_F16:** Build for Production & Deployment Strategy.

**IV. Key Considerations for Vue.js Frontend Development (Default Styling):**

*   **CSS Organization:** While scoped CSS prevents global conflicts, you still need a strategy for common styling patterns or themes. CSS Custom Properties defined in `main.css` can be very helpful for this.
*   **Maintainability of CSS:** For larger components with complex styles, the `<style scoped>` block can become large. Consider breaking down styles or using SCSS for better organization if needed.
*   **No Utility Classes:** You will be writing more CSS directly compared to using a utility-first framework. This gives more control but can also mean more time spent on styling.
*   **Component Styling Encapsulation:** This is a major benefit. Styles for one component won't accidentally leak and affect others.
*   **(Other considerations from previous Vue.js blueprint remain relevant: API Contract, State Management, Component Reusability, Performance, Error Handling, UX, Frontend Testing if added later).**

This revised blueprint focuses on leveraging Vue.js's core strengths for building a reactive UI, using its built-in mechanisms for styling. This approach can be simpler for teams not already invested in a utility-first CSS framework and provides excellent component encapsulation.

</MARKDOWN_DOCUMENT>