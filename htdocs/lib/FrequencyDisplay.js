function FrequencyDisplay(element) {
    this.element = $(element);
}

FrequencyDisplay.prototype.setFrequency = function(freq) {
    this.element.html((freq / 1e6).toLocaleString(undefined, {maximumFractionDigits: 4, minimumFractionDigits: 3}) + " MHz");
}