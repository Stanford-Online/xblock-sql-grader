/* eslint-disable no-unused-vars */
/**
 * Initialize the student view
 * @param {Object} runtime - The XBlock JS Runtime
 * @param {Object} element - The containing DOM element for this instance of the XBlock
 * @returns {undefined} nothing
 */
function SqlGrader(runtime, element) {
    /* eslint-enable no-unused-vars */
    'use strict';
    var $ = window.jQuery;
    var CodeMirror = window.CodeMirror;
    var $correctness = $('.correctness', element);
    var handlerUrl = runtime.handlerUrl(element, 'submit_query');
    var $submit = $('button.submit', element);
    var $textarea = $('textarea', element);
    var textarea = $textarea[0];
    var options = {
        value: $textarea.val(),
        mode: 'text/x-sql',
        indentUnit: 4,
        lineNumbers: true,
        indentWithTabs: true,
        smartIndent: true,
        matchBrackets: true,
        extraKeys: {
            'Ctrl-Space': 'autocomplete',
        },

        /* hintOptions: {
            tables: {
                Movie: [
                    "mID",
                    "title",
                    "year",
                    "director",
                ],
                Reviewer: [
                    "rID",
                    "name",
                ],
                Rating: [
                    "rID",
                    "mID",
                    "stars",
                    "ratingDate",
                ],
            },
        },*/
    };
    var myCodeMirror = CodeMirror.fromTextArea(textarea, options);

    /**
     * Refresh the display data after submission
     * @param {string} dataType - 'expected' or 'result'
     * @param {Object} result - an AJAX response
     * @returns {undefined} nothing
     */
    function refreshData(dataType, result) {
        var $table = $('<TABLE>');
        result[dataType].forEach(function (row) {
            var $tr = $('<TR>');
            row.forEach(function (cell) {
                var $td = $('<TD>');
                $td.text(cell);
                $tr.append($td);
            });
            $table.append($tr);
        });
        var selector = '.' + dataType + ' .tabular';
        var $container = $(selector, element);
        $container.empty();
        $container.append($table);
        var messageSelector = '.' + dataType + ' .message';
        var $message = $(messageSelector, element);
        if (result[dataType].length) {
            $message.empty();
        } else {
            $message.text('Empty result');
        }
    }

    /**
     * Check an AJAX response
     * @param {Object} result - an AJAX response
     * @returns {undefined} nothing
     */
    function checkResult(result) {
        var text = 'Incorrect';
        if (result.error) {
            text = 'Error: ';
            text += result.error;
            $correctness.addClass('error');
        } else if (result.comparison) {
            text = 'Correct';
            $correctness.removeClass('error');
        }
        $correctness.text(text);
        refreshData('expected', result);
        refreshData('result', result);
        $('.sql_verify_query', element).show();
        $('.sql_data', element).show();
    }
    $submit.click(function () {
        var query = myCodeMirror.getValue();
        $.ajax({
            type: 'POST',
            url: handlerUrl,
            data: JSON.stringify({
                query: query,
            }),
            success: checkResult,
        });
        return false;
    });
}
