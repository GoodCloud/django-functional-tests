Selenium.prototype.getHTML = function (locator) {  
    var element = this.page().findElement(locator);
    return element.innerHTML;
};
function eval_css(locator, inDocument) {
    var results = [];
    window.Sizzle(locator, inDocument, results);
    return results
}
