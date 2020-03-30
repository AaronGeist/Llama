var system = require('system');
var page = require('webpage').create();
page.onConsoleMessage = function(msg) {
  if (msg.indexOf("{\"title")== 0) {
    console.log(msg);
  }
};

page.open(system.args[1], function(status) {
  page.evaluate(function() {
    var dict = {};
    dict["title"] = DATA.comic.title;
    dict["cTitle"] = DATA.chapter.cTitle
    dict["cid"] = DATA.chapter.cid
    dict["picture"] = {};
    DATA.picture.forEach(function(item) {
      dict["picture"][item.pid] = item.url
    })

    console.log(JSON.stringify(dict))
  });
  phantom.exit();
});
