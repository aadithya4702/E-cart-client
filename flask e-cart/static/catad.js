const scrollContainer = document.querySelector(".products-catad");
const scrollLeftButton = document.querySelector(".leftcatadb");
const scrollRightButton = document.querySelector(".rightcatadb");

scrollLeftButton.addEventListener("click", () => {
  scrollContainer.scrollLeft -= 100;
});

scrollRightButton.addEventListener("click", () => {
  scrollContainer.scrollLeft += 100;
});
