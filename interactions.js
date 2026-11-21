const stage = document.querySelector("[data-tilt]");
const tiltInput = window.matchMedia("(pointer: fine) and (prefers-reduced-motion: no-preference)");

if (stage) {
  const resetTilt = () => {
    stage.style.removeProperty("--tip-x");
    stage.style.removeProperty("--tip-y");
    stage.style.removeProperty("--light-x");
    stage.style.removeProperty("--light-y");
  };

  stage.addEventListener("pointermove", (event) => {
    if (!tiltInput.matches || event.pointerType !== "mouse") return;
    const bounds = stage.parentElement.getBoundingClientRect();
    const x = (event.clientX - bounds.left) / bounds.width;
    const y = (event.clientY - bounds.top) / bounds.height;
    stage.style.setProperty("--tip-x", `${(0.5 - y) * 9}deg`);
    stage.style.setProperty("--tip-y", `${(x - 0.5) * 11}deg`);
    stage.style.setProperty("--light-x", `${x * 100}%`);
    stage.style.setProperty("--light-y", `${y * 100}%`);
  });

  stage.addEventListener("pointerleave", resetTilt);
  tiltInput.addEventListener("change", resetTilt);
}

const viewer = document.querySelector(".photo-dialog");
if (viewer && typeof viewer.showModal === "function") {
  const image = viewer.querySelector("img");
  let trigger;

  document.querySelectorAll("[data-lightbox]").forEach((link) => {
    link.addEventListener("click", (event) => {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      trigger = link;
      image.src = link.href;
      image.alt = link.querySelector("img").alt;
      viewer.showModal();
    });
  });

  viewer.querySelector("button").addEventListener("click", () => viewer.close());
  viewer.addEventListener("click", (event) => {
    if (event.target === viewer) viewer.close();
  });
  viewer.addEventListener("close", () => {
    image.removeAttribute("src");
    trigger?.focus();
  });
}
