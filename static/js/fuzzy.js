// Forgiving matching for searches people type: the project picker and the Ctrl+K search.
// wordScore(token, words) is how well one typed word matches the best of a thing's words: exactly (10),
// as its start (8), inside it (5), with one typo (4), or as an abbreviation such as 'trq' for torque (3);
// 0 when it doesn't. The same rules run in Python (projects._word_score): keep them alike.
(function (root) {
    function words(text) {
        return String(text || '').normalize('NFKD').replace(/[^\x00-\x7f]/g, '').toLowerCase().match(/[a-z0-9]+/g) || [];
    }

    function oneEditApart(a, b) {
        if (a === b) return true;
        if (Math.abs(a.length - b.length) > 1) return false;
        var i;
        if (a.length === b.length) {
            var diff = [];
            for (i = 0; i < a.length; i++) if (a[i] !== b[i]) diff.push(i);
            return diff.length === 1 || (diff.length === 2 && diff[1] === diff[0] + 1 &&
                a[diff[0]] === b[diff[1]] && a[diff[1]] === b[diff[0]]);
        }
        var s = a.length < b.length ? a : b, l = a.length < b.length ? b : a;
        for (i = 0; i < s.length && s[i] === l[i]; i++) { /* first difference */ }
        return s.slice(i) === l.slice(i + 1);
    }

    function inOrder(token, word) {
        var at = 0;
        for (var i = 0; i < token.length; i++) {
            at = word.indexOf(token[i], at);
            if (at < 0) return false;
            at += 1;
        }
        return true;
    }

    function wordScore(token, list) {
        var best = 0;
        for (var i = 0; i < list.length; i++) {
            var w = list[i], score = 0;
            if (w === token) return 10;
            if (w.indexOf(token) === 0) score = 8;
            else if (w.indexOf(token) >= 0) score = 5;
            else if (token.length >= 4 && (oneEditApart(token, w) || oneEditApart(token, w.slice(0, token.length)))) score = 4;
            else if (token.length >= 2 && w[0] === token[0] && inOrder(token, w)) score = 3;
            if (score > best) best = score;
        }
        return best;
    }

    var Fuzzy = { words: words, wordScore: wordScore };
    if (typeof module === 'object' && module.exports) module.exports = Fuzzy;     // the tests run it in Node
    else root.Fuzzy = Fuzzy;
})(this);
