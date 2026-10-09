// @vitest-environment jsdom
import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { App } from "./main";
import { api } from "./api";
const response = (data: unknown, ok = true) =>
  Promise.resolve({ ok, json: () => Promise.resolve(data) } as Response);
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
function mount(path = "/") {
  render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}
function mockSession() {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) => {
      if (url.endsWith("/session"))
        return response({ username: "operator", mode: "fixture" });
      if (url.endsWith("/status"))
        return response({ mode: "fixture", transport: "direct" });
      return response([]);
    }),
  );
}
describe("workspace journeys", () => {
  it("shows sign in when the backend rejects the session", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => response({ detail: "Sign in to continue" }, false)),
    );
    mount();
    expect(
      await screen.findByRole("heading", { name: "Sign in" }),
    ).toBeTruthy();
  });
  it("reports login failures", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        response({ detail: "Incorrect username or password" }, false),
      ),
    );
    mount();
    await screen.findByRole("heading", { name: "Sign in" });
    await userEvent.type(screen.getByLabelText("Password"), "bad");
    await userEvent.click(
      screen.getByRole("button", { name: "Enter workspace" }),
    );
    expect(await screen.findByRole("alert")).toHaveProperty(
      "textContent",
      "Incorrect username or password",
    );
  });
  it("navigates between real application areas", async () => {
    mockSession();
    mount();
    await screen.findByText("A clearer view of every event.");
    await userEvent.click(
      screen.getAllByRole("link", { name: /Knowledge Assistant/ })[0],
    );
    expect(await screen.findByText("Answers you can trace.")).toBeTruthy();
    await userEvent.click(
      screen.getByRole("link", { name: /Verification Results/ }),
    );
    expect(
      await screen.findByText("Confidence, record by record."),
    ).toBeTruthy();
  });
  it("renders loading state while restoring session", () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => new Promise(() => {})),
    );
    mount();
    expect(screen.getByRole("status").textContent).toContain("Loading");
  });
  it("renders backend errors in the knowledge view", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        url.endsWith("/session")
          ? response({ username: "operator" })
          : response({ detail: "Database unavailable" }, false),
      ),
    );
    mount("/knowledge");
    expect(await screen.findByRole("alert")).toHaveProperty(
      "textContent",
      "Database unavailable",
    );
  });
  it("restores saved messages and original evidence", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (url.endsWith("/session")) return response({ username: "operator" });
        if (url.endsWith("/conversations"))
          return response([
            { id: "saved", created_at: "2026-10-10T10:00:00Z" },
          ]);
        if (url.endsWith("/conversations/saved"))
          return response([
            {
              id: "m",
              role: "assistant",
              content: "Registration closes on 12 November.",
              evidence: [
                {
                  id: "record",
                  text: "Original source record",
                  source: { file: "events.json", record_id: "event-101" },
                },
              ],
            },
          ]);
        return response([]);
      }),
    );
    mount("/knowledge");
    expect(
      await screen.findByText("Registration closes on 12 November."),
    ).toBeTruthy();
    await userEvent.click(screen.getByText(/events.json/));
    expect(screen.getByText("Original source record")).toBeTruthy();
  });
  it("renders verification results with discrepancies", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (url.endsWith("/session")) return response({ username: "operator" });
        if (url.endsWith("/runs"))
          return response([
            {
              id: "r",
              event_id: "EVT-101",
              created_at: "2026-10-10T10:00:00Z",
              mode: "fixture",
              status: "review_required",
            },
          ]);
        if (url.endsWith("/runs/r/results"))
          return response([
            {
              id: "v",
              status: "review_required",
              record: {
                name: "Ben Jacobs",
                email: "ben@example.org",
                organization: "Northline Labs",
              },
              reasons: ["Duplicate registration messages"],
              evidence: [],
            },
          ]);
        return response([]);
      }),
    );
    mount("/results");
    expect(await screen.findByText("Ben Jacobs")).toBeTruthy();
    expect(
      screen.getAllByText("Duplicate registration messages").length,
    ).toBeGreaterThan(0);
  });
  it("clears the authenticated view after logout", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string, options: RequestInit) =>
        url.endsWith("/session")
          ? response(
              options?.method === "DELETE"
                ? { status: "signed_out" }
                : { username: "operator", mode: "fixture" },
            )
          : response([]),
      ),
    );
    mount();
    await screen.findByText("A clearer view of every event.");
    await userEvent.click(screen.getByRole("button", { name: "Sign out" }));
    expect(
      await screen.findByRole("heading", { name: "Sign in" }),
    ).toBeTruthy();
  });
  it("sends API requests with credentials", async () => {
    const fetchMock = vi.fn((_url: string, _options: RequestInit) =>
      response({ status: "ok" }),
    );
    vi.stubGlobal("fetch", fetchMock);
    await api("/health");
    expect(fetchMock.mock.calls[0]).toHaveLength(2);
    expect(fetchMock.mock.calls[0][1]).toMatchObject({
      credentials: "include",
    });
  });
});
