let rev = 0;
carousel(rev);

function previousReview() {
  rev = rev - 1;
  carousel(rev);
}

function nextReview() {
  rev = rev + 1;
  carousel(rev);
}

function carousel(review) {
  let reviews = document.getElementsByClassName("im");

  if (review >= reviews.length) {
    review = 0;
    rev = 0;
  }
  if (review < 0) {
    review = reviews.length - 1;
    rev = reviews.length - 1;
  }
  for (let i = 0; i < reviews.length; i++) {
    reviews[i].style.display = "none";
  }
  reviews[review].style.display = "block";
}

// const scrollContainer = document.querySelector(".products-catad");
// const scrollLeftButton = document.querySelector(".leftcatadb");
// const scrollRightButton = document.querySelector(".rightcatadb");

// scrollLeftButton.addEventListener("click", () => {
//   scrollContainer.scrollLeft -= 100;
// });

// scrollRightButton.addEventListener("click", () => {
//   scrollContainer.scrollLeft += 100;
// });

