import { expect, test, type Page } from "@playwright/test";

const API = process.env.SDS_API_URL ?? "http://localhost:8000";

async function outbox(kind: string, phone: string): Promise<string> {
  const res = await fetch(`${API}/api/dev/outbox?limit=500`);
  const messages = (await res.json()) as { kind: string; to: string; body: string }[];
  const m = messages.find((x) => x.kind === kind && x.to.endsWith(phone));
  if (!m) throw new Error(`no ${kind} message for ${phone}`);
  return m.body;
}

async function staffLogin(page: Page, path: string, email: string, password: string) {
  await page.goto(path);
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
}

/** Answer whatever is on screen, the way a student would, until the level is complete. */
async function playLevel(page: Page) {
  for (let step = 0; step < 400; step++) {
    await page.waitForTimeout(200);
    if (await page.getByText("Level complete!").count()) return;
    const conf = page.locator(".conf button");
    if (await conf.count()) { await conf.nth(2).click(); continue; }
    for (const name of ["Keep going", "Let's go", "I'm ready", "Done reading", "I've finished reading", "Familiar puzzle", "No thanks"]) {
      const b = page.getByRole("button", { name, exact: true });
      if (await b.count() && await b.first().isEnabled()) { await b.first().click(); break; }
    }
    if (await page.locator(".keypad").count()) {
      const next = page.getByRole("button", { name: "Next" });
      for (let i = 0; i < 15 && !(await next.isEnabled()); i++) await page.locator(".keypad button").first().click();
      await next.click();
      continue;
    }
    if (await page.locator("[role=slider]").count()) {
      const box = (await page.locator("[role=slider]").boundingBox())!;
      await page.mouse.click(box.x + box.width * 0.4, box.y + box.height / 2);
      await page.getByRole("button", { name: "Next" }).click();
      continue;
    }
    const start = page.getByRole("button", { name: "Start", exact: true });
    if (await start.count()) {
      await start.click();
      await page.waitForTimeout(1500);
      const done = page.getByRole("button", { name: "Done", exact: true });
      if (await done.count()) await done.click();
      continue;
    }
    const opts = page.locator(".opt");
    if (await opts.count()) {
      await opts.first().click();
      const next = page.getByRole("button", { name: /^(Next|Keep|Submit)$/ });
      if (await next.count() && await next.first().isEnabled()) await next.first().click();
    }
  }
  throw new Error("level did not finish");
}

test("a student plays level 1 and the answers reach the server", async ({ page }) => {
  // Meera Nair (demo) has consent but has not played yet.
  const login = await fetch(`${API}/api/auth/staff/login`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: "admin@sunrise-demo.in", password: "demo-admin-123" }),
  }).then((r) => r.json());
  const school = await fetch(`${API}/api/school`, { headers: { Authorization: `Bearer ${login.token}` } }).then((r) => r.json());
  const klass = school.classes[0];
  const roster = await fetch(`${API}/api/school/classes/${klass.id}/roster`, { headers: { Authorization: `Bearer ${login.token}` } }).then((r) => r.json());
  const meera = roster.students.find((s: any) => s.name === "Meera Nair");
  const reset = await fetch(`${API}/api/school/students/${meera.student_id}/pin`, {
    method: "POST", headers: { Authorization: `Bearer ${login.token}` },
  }).then((r) => r.json());

  await page.goto("/play");
  await page.getByLabel("Class code").fill(klass.class_code);
  await page.getByLabel("Your 4-digit PIN").fill(reset.pin);
  await page.getByRole("button", { name: "Go" }).click();
  await expect(page.getByRole("heading", { name: "Warm-up" })).toBeVisible();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByRole("heading", { name: "Your levels" })).toBeVisible();
  const level = page.locator(".level").filter({ has: page.getByRole("button", { name: /Play now|Continue/ }) }).first();
  await level.getByRole("button").click();
  await playLevel(page);
  await expect(page.getByText("Level complete!")).toBeVisible();
  await expect.poll(async () => {
    const r = await fetch(`${API}/api/school/classes/${klass.id}/roster`, { headers: { Authorization: `Bearer ${login.token}` } }).then((x) => x.json());
    return r.students.find((s: any) => s.name === "Meera Nair").sessions_completed;
  }, { timeout: 30_000 }).toBeGreaterThanOrEqual(1);
});

test("a parent signs in with an OTP and reads the report in Hindi and English", async ({ page }) => {
  await page.goto("/parent");
  await page.getByLabel(/Mobile number/).fill("9810000002");
  await page.getByRole("button", { name: "Send code" }).click();
  await page.waitForTimeout(500);
  const code = (await outbox("otp", "9810000002")).match(/\b(\d{6})\b/)![1];
  await page.getByLabel(/6-digit code/).fill(code);
  await page.getByRole("button", { name: "Verify" }).click();
  await expect(page.getByRole("heading", { name: "Kabir Khan" })).toBeVisible();
  await page.getByRole("link", { name: /View report/ }).click();
  await expect(page.getByText("Kabir Khan's learning profile")).toBeVisible();
  await expect(page.getByText("This is a screening profile, not a clinical assessment.")).toBeVisible();
  await page.getByRole("button", { name: "हिंदी" }).click();
  await expect(page.getByText("Kabir Khan की सीखने की प्रोफ़ाइल")).toBeVisible();
});

test("school staff see consent and completion; reviewers see the admin console", async ({ page }) => {
  await staffLogin(page, "/school", "admin@sunrise-demo.in", "demo-admin-123");
  await expect(page.getByRole("heading", { name: /Sunrise Public School/ })).toBeVisible();
  await expect(page.getByText(/consented/).first()).toBeVisible();
  await page.getByRole("link", { name: "Shared reports" }).click();
  await expect(page.getByRole("cell", { name: "Riya Sharma" })).toBeVisible();
  await expect(page.getByRole("cell", { name: "Kabir Khan" })).toHaveCount(0); // not shared by the parent

  await staffLogin(page, "/admin", "superadmin@revenuelogy-demo.in", "demo-super-123");
  await expect(page.getByRole("heading", { name: "Review queue" })).toBeVisible();
  await page.getByRole("link", { name: "Item bank" }).click();
  await expect(page.getByText(/items$/)).toBeVisible();
  await page.getByRole("link", { name: "Scoring" }).click();
  await expect(page.getByRole("cell", { name: "1.0.0" })).toBeVisible();
});
