(function(){
  'use strict';
  if(!/(?:^|[?&])caya=1(?:&|$)/.test(window.location.search)){return;}
  fetch('/caya/caya-app.html', {cache: 'no-store', credentials: 'same-origin'})
    .then(function(response){
      if(!response.ok){throw new Error('CaYaRouter kabuğu yüklenemedi: HTTP ' + response.status);}
      return response.text();
    })
    .then(function(page){
      document.open();
      document.write(page);
      document.close();
    })
    .catch(function(error){
      document.body.innerHTML = '<p style="font-family:Arial;padding:20px">' + String(error.message || error) + '</p>';
    });
})();
