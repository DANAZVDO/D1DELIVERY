(function() {
    var ctx = null;

    function getCtx() {
        if (!ctx) {
            try { ctx = new (window.AudioContext || window.webkitAudioContext)(); } catch(e) { return null; }
        }
        if (ctx.state === 'suspended') ctx.resume();
        return ctx;
    }

    function play(freq, duration, type, vol, ramp) {
        var c = getCtx();
        if (!c) return;
        try {
            var osc = c.createOscillator();
            var gain = c.createGain();
            osc.type = type || 'sine';
            osc.frequency.setValueAtTime(freq, c.currentTime);
            gain.gain.setValueAtTime(vol || 0.15, c.currentTime);
            if (ramp) gain.gain.exponentialRampToValueAtTime(0.001, c.currentTime + duration);
            else gain.gain.setValueAtTime(0, c.currentTime + duration);
            osc.connect(gain);
            gain.connect(c.destination);
            osc.start(c.currentTime);
            osc.stop(c.currentTime + duration);
        } catch(e) {}
    }

    function playChord(freqs, duration, type, vol) {
        freqs.forEach(function(f, i) {
            setTimeout(function() { play(f, duration, type, vol); }, i * 30);
        });
    }

    window.Sounds = {
        addToCart: function() {
            play(880, 0.1, 'sine', 0.12);
            setTimeout(function() { play(1100, 0.12, 'sine', 0.12); }, 50);
        },

        removeFromCart: function() {
            play(440, 0.1, 'sine', 0.08);
        },

        openCart: function() {
            play(600, 0.1, 'sine', 0.1);
            setTimeout(function() { play(750, 0.08, 'sine', 0.08); }, 40);
        },

        placeOrder: function() {
            playChord([523, 659, 784], 0.25, 'sine', 0.15);
            setTimeout(function() { play(1047, 0.4, 'sine', 0.15, true); }, 150);
        },

        paymentSuccess: function() {
            playChord([660, 830, 990], 0.3, 'sine', 0.15);
            setTimeout(function() { play(1320, 0.5, 'sine', 0.18, true); }, 200);
        },

        click: function() {
            play(1000, 0.05, 'square', 0.06);
        },

        buttonHover: function() {
            play(1200, 0.03, 'sine', 0.04);
        }
    };
})();
