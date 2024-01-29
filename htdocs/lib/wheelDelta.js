/*
 * Normalize scroll wheel events.
 *
 * It seems like there's no consent as to how mouse wheel events are presented in the javascript API. The standard
 * states that a MouseEvent has a deltaY property that contains the scroll distances, together with a deltaMode
 * property that state the "unit" that deltaY has been measured in. The deltaMode can be either pixels, lines or
 * pages. The latter is seldomly used in practise.
 *
 * The troublesome part is that there is no standard on how to correlate the two at this point.
 *
 * The basic idea is that one tick of a mouse wheel results in a total return value of +/- 1 from this method.
 * It's important to keep in mind that one tick of a wheel may result in multiple events in the browser. The aim
 * of this method is to scale the sum of deltaY over
 */
function wheelDelta(evt) {
    if ('deltaMode' in evt && evt.deltaMode === WheelEvent.DOM_DELTA_PIXEL) {
        // chrome and webkit-based browsers seem to correlate one tick of the wheel to 120 pixels.
        return evt.deltaY / 120;
    }
    // firefox seems to scroll at an interval of 6 lines per wheel tick
    return evt.deltaY / 6;
}
