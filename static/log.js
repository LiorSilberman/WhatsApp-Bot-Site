$(document).ready(function() {
    const images = [
      'static/cool-background.png',
      'static/pexels-james-wheeler-1519088.jpg',
      'static/pexels-quintin-gellar-313782.jpg',
      'static/pexels-stein-egil-liland-1933239.jpg',
      'static/tobias-reich-JLl83G_pFpc-unsplash.jpg',
    ];

    const randomImage = images[Math.floor(Math.random() * images.length)];
    document.body.style.backgroundImage = `url(${randomImage})`;
});