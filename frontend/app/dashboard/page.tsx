// app/dashboard/page.tsx
// Redirects to the new unified home page.
// The old 9-agent dashboard has been replaced by app/page.tsx.

import { redirect } from "next/navigation";

export default function DashboardPage() {
  redirect("/");
}
