/* globals $ */

var ChronAmSearch = {};

(function() {
    var highlightNoiseRegEx = new RegExp(
        /^[/.,/#!$%^&*;:{}=\-_`~()]+|[/.,/#!$%^&*;:{}=\-_`~()]+$|'s$/
    );
    ChronAmSearch.highlightNoiseRegEx = highlightNoiseRegEx;

    ChronAmSearch.matchWords = function(searchWords, all_coordinates) {
        var matchedWords = [];

        $.each(searchWords.split(" "), function(index, word) {
            // don't do anything if the word is blank
            if (word) {
                word = word.toLocaleLowerCase().trim();

                for (var word_on_page in all_coordinates["coords"]) {
                    var match_word = word_on_page
                        .toLocaleLowerCase()
                        .replace(highlightNoiseRegEx, " ")
                        .replace(/\s+/, " ")
                        .trim();

                    if (
                        match_word === word &&
                        matchedWords.indexOf(word_on_page) < 0
                    ) {
                        matchedWords.push(word_on_page);
                    }
                }
            }
        });
        return matchedWords;
    };
})();
