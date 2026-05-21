/**
 * Unit tests for DemoRegisterModal.vue.
 *
 * The modal's only non-trivial logic is `registerHref`: it appends the demo
 * session UUID as a `ref` query param so the parent platform's signup page
 * can claim the demo row on registration. We also cover the empty-URL guard
 * and the close-button emission, since those are the contracts the demo
 * workspace (frontend/pages/index.vue) relies on.
 *
 * Note: the template uses <Teleport to="body">, so rendered DOM lives on
 * document.body — not inside the test wrapper's element tree. We query the
 * document directly rather than via wrapper.find().
 */

import { afterEach, describe, it, expect } from "vitest";
import { mount, VueWrapper } from "@vue/test-utils";
import DemoRegisterModal from "../../components/chat/helper/DemoRegisterModal.vue";

const baseProps = {
  isOpen: true,
  interactionCount: 12,
  interactionLimit: 15,
  registerUrl: "https://portal.tgsaapp.com/signup",
  sessionId: "11111111-2222-3333-4444-555555555555",
};

let mounted: VueWrapper | null = null;

function mountModal(overrides: Partial<typeof baseProps> = {}) {
  mounted = mount(DemoRegisterModal, {
    props: { ...baseProps, ...overrides },
    attachTo: document.body,
  });
  return mounted;
}

afterEach(() => {
  mounted?.unmount();
  mounted = null;
  document.body.innerHTML = "";
});

function ctaHref(): string {
  // The CTA is the only <a> element in the teleported modal.
  const link = document.body.querySelector("a[href]") as HTMLAnchorElement | null;
  return link?.getAttribute("href") ?? "";
}

describe("DemoRegisterModal — registerHref", () => {
  it("appends the session id as a ref query param", () => {
    mountModal();
    expect(ctaHref()).toBe(
      "https://portal.tgsaapp.com/signup?ref=11111111-2222-3333-4444-555555555555",
    );
  });

  it("falls back to '#' when registerUrl is empty so the link is inert", () => {
    mountModal({ registerUrl: "" });
    expect(ctaHref()).toBe("#");
  });

  it("omits the ref param when sessionId is empty", () => {
    mountModal({ sessionId: "" });
    expect(ctaHref()).toBe("https://portal.tgsaapp.com/signup");
  });

  it("preserves existing query params on registerUrl", () => {
    mountModal({
      registerUrl: "https://portal.tgsaapp.com/signup?utm_source=demo",
    });
    const href = ctaHref();
    expect(href).toContain("utm_source=demo");
    expect(href).toContain("ref=11111111-2222-3333-4444-555555555555");
  });
});

describe("DemoRegisterModal — completion %", () => {
  it("renders interactionCount / interactionLimit and percent", () => {
    mountModal({ interactionCount: 9, interactionLimit: 15 });
    const text = document.body.textContent ?? "";
    expect(text).toContain("9");
    expect(text).toContain("15");
    expect(text).toContain("60%");
  });

  it("caps the percent at 100 when count exceeds limit", () => {
    mountModal({ interactionCount: 30, interactionLimit: 15 });
    expect(document.body.textContent).toContain("100%");
  });

  it("returns 0% when limit is zero (avoids divide-by-zero)", () => {
    mountModal({ interactionCount: 5, interactionLimit: 0 });
    expect(document.body.textContent).toContain("0%");
  });
});

describe("DemoRegisterModal — close behaviour", () => {
  it("emits 'close' and flips v-model when the close (X) button is clicked", async () => {
    const wrapper = mountModal();
    // The header X-button is the first <button> rendered into body.
    const closeBtn = document.body.querySelector("button[type='button']") as HTMLButtonElement;
    closeBtn.click();
    await wrapper.vm.$nextTick();
    expect(wrapper.emitted("close")).toBeTruthy();
    expect(wrapper.emitted("update:isOpen")?.[0]).toEqual([false]);
  });

  it("renders nothing when isOpen is false", () => {
    mountModal({ isOpen: false });
    expect(document.body.querySelector("a[href]")).toBeNull();
    expect(document.body.querySelector("button[type='button']")).toBeNull();
  });
});
