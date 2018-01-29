# son-bss  [![Build Status](http://jenkins.sonata-nfv.eu/buildStatus/icon?job=son-bss)](http://jenkins.sonata-nfv.eu/job/son-bss)

Very simple gui that allows customers to retrieve and inspect Network Services and additionally allows to request instantiations on them.

## Development

To contribute to the development of the SONATA BSS, you may use the very same development workflow as for any other SONATA Github project. That is, you have to fork the repository and create pull requests.

### Building

Build Docker container image
* docker build --no-cache -t son-yo-gen-bss . 

### Dependencies

Bower dependencies:

* [angular](https://github.com/angular/angular.js) >=1.5.7 (MIT)
* [angular-json-tree](https://github.com/awendland/angular-json-tree) >=1.0.1 (MIT)
* [angular-animate](https://github.com/angular/angular.js) >=1.5.7 (MIT)
* [angular-formly-templates-bootstrap](https://github.com/formly-js/angular-formly-templates-bootstrap) >=6.3.2 (MIT)
* [angular-formly](https://github.com/formly-js/angular-formly) >=8.2.1 (MIT)
* [angular-mocks](https://github.com/angular/angular.js) >=1.5.7 (MIT)
* [angular-ui-router] >=0.3.1 (MIT)
* [api-check](https://github.com/kentcdodds/apiCheck.js) >=7.5.5 (MIT)
* [bootstrap](http://getbootstrap.com) >=3.3.6 (MIT)
* [jquery] (MIT)

Npm dependencies:

* [abbrev](https://github.com/isaacs/abbrev-js) >=1.0.9 (ISC)
* [accepts](https://github.com/jshttp/accepts) >=1.3.3 (MIT)
* [adm-zip](https://github.com/cthackers/adm-zip) >=0.4.7 (MIT)
* [agent-base](https://github.com/TooTallNate/node-agent-base) >=2.0.1 (MIT)
* [amdefine](https://github.com/jrburke/amdefine) >=1.0.0 (BSD-3-Clause AND MIT)
* [ansi-regex](https://github.com/sindresorhus/ansi-regex) >=2.0.0 (MIT)
* [ansi-styles](https://github.com/chalk/ansi-styles) >=2.2.1 (MIT)
* [argparse](https://github.com/nodeca/argparse) >=0.1.16 (MIT)
* [arr-diff](https://github.com/jonschlinkert/arr-diff) >=2.0.0 (MIT)
* [arr-flatten](https://github.com/jonschlinkert/arr-flatten) >=1.0.1 (MIT)
* [array-unique](https://github.com/jonschlinkert/array-unique) >=0.2.1 (MIT)
* [asn1](https://github.com/mcavage/node-asn1)>=0.2.3 (MIT)
* [assert-plus](https://github.com/mcavage/node-assert-plus) >=1.0.0 (MIT)
* [async](https://github.com/caolan/async) >=1.5.2 (MIT)
* [aws-sign2](https://github.com/mikeal/aws-sign) >=0.6.0 (Apache-2.0)
* [balanced-match](https://github.com/juliangruber/balanced-match) >=0.4.1 (MIT)
* [basic-auth](https://github.com/jshttp/basic-auth) >=1.0.4 (MIT)
* [batch](https://github.com/visionmedia/batch) >=0.5.3 (MIT)
* [bl](https://github.com/rvagg/bl) >=1.0.3 (MIT)
* [body-parser](https://github.com/expressjs/body-parser) >=1.14.2 (MIT)
* [boom](https://github.com/hapijs/boom) >=2.10.1 (BSD-3-Clause)
* [brace-expansion](https://github.com/juliangruber/brace-expansion) >=1.1.5 (MIT)
* [braces](https://github.com/jonschlinkert/braces) >=1.8.5 (MIT)
* [buffer-crc32](https://github.com/brianloveswords/buffer-crc32) >=0.2.1 (UNKNOWN)
* [bytes](https://github.com/visionmedia/bytes.js) >=2.4.0 (MIT)
* [caseless](https://github.com/mikeal/caseless) >=0.11.0 (Apache-2.0)
* [chalk](https://github.com/chalk/chalk) >=1.1.3 (MIT)
* [coffee-script](https://github.com/jashkenas/coffee-script) >=1.3.3 (MIT)
* [colors](https://github.com/Marak/colors.js) >=0.6.2 (MIT)
* [combined-stream](https://github.com/felixge/node-combined-stream) >=1.0.5 (MIT)
* [commander](https://github.com/tj/commander.js) >=2.9.0 (MIT)
* [concat-map](https://github.com/substack/node-concat-map) >=0.0.1 (MIT)
* [concat-stream](https://github.com/maxogden/concat-stream) >=1.5.0 (MIT)
* [connect-livereload](https://github.com/intesso/connect-livereload) >=0.5.4 (MIT)
* [connect](https://github.com/senchalabs/connect) >=3.4.1 (MIT)
* [content-type](https://github.com/jshttp/content-type) >=1.0.2 (MIT)
* [cookie-signature] >=1.0.1 (UNKNOWN)
* [cookie](https://github.com/shtylman/node-cookie) >=0.0.5 (UNKNOWN)
* [core-util-is](https://github.com/isaacs/core-util-is) >=1.0.2 (MIT)
* [cryptiles](https://github.com/hapijs/cryptiles) >=2.0.5 (BSD-3-Clause)
* [dashdash](https://github.com/trentm/node-dashdash) >=1.14.0 (MIT)
* [dateformat] 1.0.2-1.2.3 (UNKNOWN)
* [debug](https://github.com/visionmedia/debug) >=2.2.0 (MIT)
* [delayed-stream](https://github.com/felixge/node-delayed-stream) >=1.0.0 (MIT)
* [depd](https://github.com/dougwilson/nodejs-depd) >=1.1.0 (MIT)
* [destroy](https://github.com/stream-utils/destroy) >=1.0.4 (MIT)
* [ecc-jsbn](https://github.com/quartzjer/ecc-jsbn) >=0.1.1 (MIT)
* [ee-first](https://github.com/jonathanong/ee-first) >=1.1.1 (MIT)
* [encodeurl](https://github.com/pillarjs/encodeurl) >=1.0.1 (MIT)
* [escape-html](https://github.com/component/escape-html) >=1.0.3 (MIT)
* [escape-string-regexp](https://github.com/sindresorhus/escape-string-regexp) >=1.0.5 (MIT)
* [esprima](https://github.com/ariya/esprima) >=1.0.4 (BSD)
* [etag](https://github.com/jshttp/etag) >=1.7.0 (MIT)
* [eventemitter2](https://github.com/hij1nx/EventEmitter2) >=0.4.14 (MIT)
* [exit](https://github.com/cowboy/node-exit) >=0.1.2 (MIT)
* [expand-brackets](https://github.com/jonschlinkert/expand-brackets) >=0.1.5 (MIT)
* [expand-range](https://github.com/jonschlinkert/expand-range) >=1.8.2 (MIT)
* [extend](https://github.com/justmoon/node-extend) >=3.0.0 (MIT)
* [extglob](https://github.com/jonschlinkert/extglob) >=0.3.2 (MIT)
* [extract-zip](https://github.com/maxogden/extract-zip) >=1.5.0 (BSD-2-Clause)
* [extsprintf](https://github.com/davepacheco/node-extsprintf) >=1.0.2 (MIT)
* [faye-websocket](https://github.com/faye/faye-websocket-node) >=0.10.0 (MIT)
* [fd-slicer](https://github.com/andrewrk/node-fd-slicer) >=1.0.1 (MIT)
* [filename-regex](https://github.com/regexps/filename-regex) >=2.0.0 (MIT)
* [fill-range](https://github.com/jonschlinkert/fill-range) >=2.2.3 (MIT)
* [finalhandler](https://github.com/pillarjs/finalhandler) >=0.4.1 (MIT)
* [findup-sync](https://github.com/cowboy/node-findup-sync)>=0.3.0 (MIT)
* [for-in](https://github.com/jonschlinkert/for-in) >=0.1.5 (MIT)
* [for-own](https://github.com/jonschlinkert/for-own) >=0.1.4 (MIT)
* [forever-agent](https://github.com/mikeal/forever-agent) >=0.6.1 (Apache-2.0)
* [form-data](https://github.com/form-data/form-data) >=1.0.0-rc4 (MIT)
* [formidable](https://github.com/felixge/node-formidable) >=1.0.14 (MIT*)
* [fresh](https://github.com/jshttp/fresh) >=0.3.0 (MIT)
* [fs-extra](https://github.com/jprichardson/node-fs-extra) >=0.26.7 (MIT)
* [fs.realpath](https://github.com/isaacs/fs.realpath) >=1.0.0 (ISC)
* [gaze](https://github.com/shama/gaze) >=1.1.0 (MIT)
* [generate-function](https://github.com/mafintosh/generate-function) >=2.0.0 (MIT)
* [generate-object-property](https://github.com/mafintosh/generate-object-property) >=1.2.0 (MIT)
* [getobject](https://github.com/cowboy/node-getobject) >=0.1.0 (MIT)
* [getpass](https://github.com/arekinath/node-getpass) >=0.1.6 (MIT)
* [glob-base](https://github.com/jonschlinkert/glob-base) >=0.3.0 (MIT)
* [glob-parent](https://github.com/es128/glob-parent) >=2.0.0 (ISC)
* [glob](https://github.com/isaacs/node-glob) >=7.0.5 (ISC)
* [globule](https://github.com/cowboy/node-globule) >=1.0.0 (MIT)
* [graceful-fs](https://github.com/isaacs/node-graceful-fs) >=4.1.4 (ISC)
* [graceful-readlink](https://github.com/zhiyelee/graceful-readlink) >=1.0.1 (MIT)
* [grunt-connect](https://github.com/iammerrick/grunt-connect) >=0.2.0 (MIT)
* [grunt-contrib-connect](https://github.com/gruntjs/grunt-contrib-connect) >=1.0.2 (MIT)
* [grunt-contrib-watch](https://github.com/gruntjs/grunt-contrib-watch) >=1.0.0 (MIT)
* [grunt-legacy-log-utils](https://github.com/gruntjs/grunt-legacy-log-utils) >=0.1.1 (MIT)
* [grunt-legacy-log](https://github.com/gruntjs/grunt-legacy-log) >=0.1.3 (MIT)
* [grunt-legacy-util](https://github.com/gruntjs/grunt-legacy-util) >=0.2.0 (MIT)
* [grunt-ng-constant](https://github.com/werk85/grunt-ng-constant) >=2.0.1 (MIT)
* [grunt-parallel-behat](https://github.com/linusnorton/grunt-parallel-behat) >=1.0.0 (MIT)
* [grunt-protractor-runner](https://github.com/teerapap/grunt-protractor-runner) >=3.2.0 (MIT)
* [grunt-protractor-webdriver](https://github.com/seckardt/grunt-protractor-webdriver) >=0.2.5 (MIT)
* [grunt-shell-spawn](https://github.com/cri5ti/grunt-shell-spawn) >=0.3.10 (MIT)
* [grunt-shell](https://github.com/sindresorhus/grunt-shell) >=1.3.0 (MIT)
* [grunt](https://github.com/gruntjs/grunt) >=0.4.5 (MIT)
* [har-validator](https://github.com/ahmadnassri/har-validator) >=2.0.6 (ISC)
* [has-ansi](https://github.com/sindresorhus/has-ansi) >=2.0.0 (MIT)
* [hasha](https://github.com/sindresorhus/hasha) >=2.2.0 (MIT)
* [hat](https://github.com/substack/node-hat) >=0.0.3 (MIT/X11)
* [hawk](https://github.com/hueniverse/hawk) >=3.1.3 (BSD-3-Clause)
* [hoek](https://github.com/hapijs/hoek) >=2.16.3 (BSD-3-Clause)
* [hooker](https://github.com/cowboy/javascript-hooker) >=0.2.3 (MIT)
* [http-errors](https://github.com/jshttp/http-errors) >=1.5.0 (MIT)
* [http-signature](https://github.com/joyent/node-http-signature) >=1.1.1 (MIT)
* [http2](https://github.com/molnarg/node-http2) >=3.3.4 (MIT)
* [https-proxy-agent](https://github.com/TooTallNate/node-https-proxy-agent) >=1.0.0 (MIT)
* [iconv-lite](https://github.com/ashtuchkin/iconv-lite) >=0.4.13 (MIT)
* [inflight](https://github.com/npm/inflight) >=1.0.5 (ISC)
* [inherits](https://github.com/isaacs/inherits) >=2.0.1 (ISC)
* [is-buffer](https://github.com/feross/is-buffer) >=1.1.3 (MIT)
* [is-dotfile](https://github.com/jonschlinkert/is-dotfile) >=1.0.2 (MIT)
* [is-equal-shallow](https://github.com/jonschlinkert/is-equal-shallow) >=0.1.3 (MIT)
* [is-extendable](https://github.com/jonschlinkert/is-extendable) >=0.1.1 (MIT)
* [is-extglob](https://github.com/jonschlinkert/is-extglob) >=1.0.0 (MIT)
* [is-glob](https://github.com/jonschlinkert/is-glob) >=2.0.1 (MIT)
* [is-my-json-valid](https://github.com/mafintosh/is-my-json-valid) >=2.13.1 (MIT)
* [is-number](https://github.com/jonschlinkert/is-number) >=2.1.0 (MIT)
* [is-posix-bracket](https://github.com/jonschlinkert/is-posix-bracket) >=0.1.1 (MIT)
* [is-primitive](https://github.com/jonschlinkert/is-primitive) >=2.0.0 (MIT)
* [is-property](https://github.com/mikolalysenko/is-property) >=1.0.2 (MIT)
* [is-stream](https://github.com/sindresorhus/is-stream) >=1.1.0 (MIT)
* [is-typedarray](https://github.com/hughsk/is-typedarray) >=1.0.0 (MIT)
* [isarray](https://github.com/juliangruber/isarray) >=1.0.0 (MIT)
* [isexe](https://github.com/isaacs/isexe) >=1.1.2 (ISC)
* [isobject](https://github.com/jonschlinkert/isobject) >=2.1.0 (MIT)
* [isstream](https://github.com/rvagg/isstream) >=0.1.2 (MIT)
* [jasmine-core](https://github.com/jasmine/jasmine) >=2.4.1 (MIT)
* [jasmine](https://github.com/jasmine/jasmine-npm) >=2.4.1 (MIT)
* [jasminewd2](https://github.com/angular/jasminewd) >=0.0.9 (MIT)
* [jju](https://github.com/rlidwka/jju) >=1.3.0 (WTFPL)
* [jodid25519](https://github.com/meganz/jodid25519) >=1.0.2 (MIT)
* [js-yaml](https://github.com/nodeca/js-yaml) >=2.0.5 (MIT)
* [jsbn](https://github.com/andyperlitch/jsbn) >=0.1.0 (BSD)
* [json-schema](AFLv2.1¦BSD) >=0.2.2 (licenses¦  )
* [json-stringify-safe](https://github.com/isaacs/json-stringify-safe) >=5.0.1 (ISC)
* [jsonfile](https://github.com/jprichardson/node-jsonfile) >=2.3.1 (MIT)
* [jsonpointer](https://github.com/janl/node-jsonpointer) >=2.0.0 (MIT)
* [jsprim](https://github.com/davepacheco/node-jsprim) >=1.3.0 (MIT)
* [kew](https://github.com/Medium/kew) >=0.7.0 (Apache-2.0)
* [kind-of](https://github.com/jonschlinkert/kind-of) >=3.0.3 (MIT)
* [klaw](https://github.com/jprichardson/node-klaw) >=1.3.0 (MIT)
* [livereload-js](https://github.com/zaius/livereload-js) >=2.2.2 (MIT)
* [lodash](https://github.com/lodash/lodash) >=4.13.1 (MIT)
* [lru-cache](https://github.com/isaacs/node-lru-cache) >=2.7.3 (ISC)
* [matchdep](https://github.com/tkellen/node-matchdep) >=1.0.1 (MIT)
* [media-typer](https://github.com/jshttp/media-typer) >=0.3.0 (MIT)
* [merge](https://github.com/yeikos/js.merge) >=1.2.0 (MIT)
* [micromatch](https://github.com/jonschlinkert/micromatch) >=2.3.10 (MIT)
* [mime-db](https://github.com/jshttp/mime-db) >=1.23.0 (MIT)
* [mime-types](https://github.com/jshttp/mime-types) >=2.1.11 (MIT)
* [mime](https://github.com/broofa/node-mime) >=1.3.4 (MIT)
* [minimatch](https://github.com/isaacs/minimatch) >=3.0.2 (ISC)
* [minimist](https://github.com/substack/minimist) >=0.0.10 (MIT)
* [mkdirp](https://github.com/substack/node-mkdirp) >=0.5.0 (MIT)
* [morgan](https://github.com/expressjs/morgan) >=1.7.0 (MIT)
* [ms](https://github.com/guille/ms.js) >=0.7.1 (MIT*)
* [negotiator](https://github.com/jshttp/negotiator) >=0.6.1 (MIT)
* [node-uuid](https://github.com/broofa/node-uuid) >=1.4.7 (MIT)
* [nopt](https://github.com/isaacs/nopt) >=1.0.10 (MIT)
* [normalize-path](https://github.com/jonschlinkert/normalize-path) >=2.0.1 (MIT)
* [npm-run-path](https://github.com/sindresorhus/npm-run-path) >=1.0.0 (MIT)
* [oauth-sign](https://github.com/mikeal/oauth-sign) >=0.8.2 (Apache-2.0)
* [object-assign](https://github.com/sindresorhus/object-assign) >=4.1.0 (MIT)
* [object.omit](https://github.com/jonschlinkert/object.omit) >=2.0.0 (MIT)
* [on-finished](https://github.com/jshttp/on-finished) >=2.3.0 (MIT)
* [on-headers](https://github.com/jshttp/on-headers) >=1.0.1 (MIT)
* [once](https://github.com/isaacs/once) >=1.3.3 (ISC)
* [opn](https://github.com/sindresorhus/opn) >=4.0.2 (MIT)
* [optimist](https://github.com/substack/node-optimist) >=0.6.1 (MIT/X11)
* [options](https://github.com/einaros/options.js) >=0.0.6 (UNKNOWN)
* [parse-glob](https://github.com/jonschlinkert/parse-glob) >=3.0.4 (MIT)
* [parseurl](https://github.com/pillarjs/parseurl) >=1.3.1 (MIT)
* [path-is-absolute](https://github.com/sindresorhus/path-is-absolute) >=1.0.0 (MIT)
* [path-key](https://github.com/sindresorhus/path-key) >=1.0.0 (MIT)
* [pause] >=0.0.1 (UNKNOWN)
* [pend](https://github.com/andrewrk/node-pend) >=1.2.0 (MIT)
* [phantomjs-prebuilt](https://github.com/Medium/phantomjs) >=2.1.7 (Apache-2.0)
* [pinkie-promise](https://github.com/floatdrop/pinkie-promise) >=2.0.1 (MIT)
* [pinkie](https://github.com/floatdrop/pinkie) >=2.0.4 (MIT)
* [portscanner](https://github.com/baalexander/node-portscanner) >=1.0.0 (MIT)
* [preserve](https://github.com/jonschlinkert/preserve) >=0.2.0 (MIT)
* [process-nextick-args](https://github.com/calvinmetcalf/process-nextick-args) >=1.0.7 (MIT)
* [progress](https://github.com/visionmedia/node-progress) >=1.1.8 (MIT*)
* [protractor-jasmine2-html-reporter](https://github.com/Kenzitron/protractor-jasmine2-html-reporter) >=0.0.6 (BSD-2-Clause)
* [protractor](https://github.com/angular/protractor) >=3.3.0 (MIT)
* [q](https://github.com/kriskowal/q) >=1.4.1 (MIT)
* [qs](https://github.com/hapijs/qs) >=5.2.0 (BSD-3-Clause)
* [randomatic](https://github.com/jonschlinkert/randomatic) >=1.1.5 (MIT)
* [range-parser](https://github.com/jshttp/range-parser) >=1.2.0 (MIT)
* [raw-body](https://github.com/stream-utils/raw-body) >=2.1.7 (MIT)
* [readable-stream](https://github.com/nodejs/readable-stream) >=2.0.6 (MIT)
* [regex-cache](https://github.com/jonschlinkert/regex-cache) >=0.4.3 (MIT)
* [repeat-element](https://github.com/jonschlinkert/repeat-element) >=1.1.2 (MIT)
* [repeat-string](https://github.com/jonschlinkert/repeat-string) >=1.5.4 (MIT)
* [request-progress](https://github.com/IndigoUnited/node-request-progress) >=2.0.1 (MIT)
* [request](https://github.com/request/request) >=2.67.0 (Apache-2.0)
* [resolve](https://github.com/substack/node-resolve) >=1.1.7 (MIT)
* [rimraf](https://github.com/isaacs/rimraf) >=2.2.8 (MIT)
* [saucelabs](https://github.com/holidayextras/node-saucelabs) >=1.0.1 (UNKNOWN)
* [sax](https://github.com/isaacs/sax-js) >=1.2.1 (ISC)
* [selenium-webdriver](https://github.com/SeleniumHQ/selenium) >=2.52.0 (Apache-2.0)
* [semver](https://github.com/npm/node-semver) >=5.0.3 (ISC)
* [send](https://github.com/pillarjs/send) >=0.14.1 (MIT)
* [serve-index](https://github.com/expressjs/serve-index) >=1.8.0 (MIT)
* [serve-static](https://github.com/expressjs/serve-static) >=1.11.1 (MIT)
* [setprototypeof](https://github.com/wesleytodd/setprototypeof) >=1.0.1 (ISC)
* [sigmund](https://github.com/isaacs/sigmund) >=1.0.1 (ISC)
* [sntp](https://github.com/hueniverse/sntp) >=1.0.9 (BSD)
* [source-map-support](https://github.com/evanw/node-source-map-support) >=0.4.1 (MIT)
* [source-map](https://github.com/mozilla/source-map) >=0.1.32 (BSD)
* [split](https://github.com/dominictarr/split) >=1.0.0 (MIT)
* [sshpk](https://github.com/arekinath/node-sshpk) >=1.8.3 (MIT)
* [stack-trace](https://github.com/felixge/node-stack-trace) >=0.0.9 (MIT*)
* [statuses](https://github.com/jshttp/statuses) >=1.3.0 (MIT)
* [string.prototype.startswith](https://github.com/mathiasbynens/String.prototype.startsWith) >=0.2.0 (MIT)
* [string_decoder](https://github.com/rvagg/string_decoder) >=0.10.31 (MIT)
* [stringstream](https://github.com/mhart/StringStream) >=0.0.5 (MIT)
* [strip-ansi](https://github.com/chalk/strip-ansi) >=3.0.1 (MIT)
* [supports-color](https://github.com/chalk/supports-color) >=2.0.0 (MIT)
* [sync-exec](https://github.com/gvarsanyi/sync-exec) >=0.6.2 (MIT)
* [throttleit](https://github.com/component/throttle) >=1.0.0 (MIT)
* [through2](https://github.com/rvagg/through2) >=2.0.1 (MIT)
* [through](https://github.com/dominictarr/through) >=2.3.8 (MIT)
* [tiny-lr](https://github.com/mklabs/tiny-lr) >=0.2.1 (MIT)
* [tmp](https://github.com/raszi/node-tmp) >=0.0.24 (MIT)
* [tosource](https://github.com/marcello3d/node-tosource) >=1.0.0 (UNKNOWN)
* [tough-cookie](https://github.com/SalesforceEng/tough-cookie) >=2.2.2 (BSD-3-Clause)
* [tunnel-agent](https://github.com/mikeal/tunnel-agent) >=0.4.3 (Apache-2.0)
* [tweetnacl](https://github.com/dchest/tweetnacl-js) >=0.13.3 (Public domain)
* [type-is](https://github.com/jshttp/type-is) >=1.6.13 (MIT)
* [typedarray](https://github.com/substack/typedarray) >=0.0.6 (MIT)
* [ultron](https://github.com/unshiftio/ultron) >=1.0.2 (MIT)
* [underscore.string](https://github.com/epeli/underscore.string) >=2.4.0 (MIT)
* [underscore](https://github.com/jashkenas/underscore) >=1.7.0 (MIT)
* [unpipe](https://github.com/stream-utils/unpipe) >=1.0.0 (MIT)
* [util-deprecate](https://github.com/TooTallNate/util-deprecate) >=1.0.2 (MIT)
* [utils-merge](https://github.com/jaredhanson/utils-merge) >=1.0.0 (MIT)
* [verror](https://github.com/davepacheco/node-verror) >=1.3.6 (MIT*)
* [websocket-driver](https://github.com/faye/websocket-driver-node) >=0.6.5 (MIT)
* [websocket-extensions](https://github.com/faye/websocket-extensions-node) >=0.1.1 (MIT)
* [which](https://github.com/isaacs/node-which) >=1.2.10 (ISC)
* [wordwrap](https://github.com/substack/node-wordwrap) >=0.0.3 (MIT)
* [wrappy](https://github.com/npm/wrappy) >=1.0.2 (ISC)
* [ws](https://github.com/websockets/ws) >=1.1.1 (MIT)
* [xml2js](https://github.com/Leonidas-from-XIV/node-xml2js) >=0.4.15 (MIT)
* [xmlbuilder](https://github.com/oozcitak/xmlbuilder-js) >=8.2.2 (MIT)
* [xtend](https://github.com/Raynos/xtend) >=4.0.1 (MIT)
* [yauzl](https://github.com/thejoshwolfe/yauzl) >=2.4.1 (MIT)

### Contributing

You may contribute to the editor similar to other SONATA (sub-) projects, i.e. by creating pull requests.

## Installation

The installation of this component can be done using the [son-install](https://github.com/sonata-nfv/son-install) script.

Grunt command line options are:

options		  				| Required		| Default value 	| Description
--------------------------- | ------------- | ----------------- | --------------------
gkApiUrl	  				| Yes 			| 					| Gatekeeper REST API Url
suite		  				| No			|					| Testing purpose: select the test suite
hostname	  				| No			| localhost			| Testing purpose: set the test hostname
protocol	  				| No			| http				| http/https selection
userManagementEnabled		| No 			| true				| Enables the use of Gatekeeper's User Management module
licenseManagementEnabled	| No 			| true				| Enables the use of Gatekeeper's License Management module

## Usage

The GUI has a principal page with an upper menu that shows the following sections:

**Available Network Services** 

In this section is possible:
* to retrieve a list of Network services availables to be instantiated ("get" operation)
* to view the NSD details (tree view)
* to instantiate an specific NSD ("post" operation)
* to get a private license to allow the instantiation process

**Requests** 

In this section is possible:
* to retrieve a list of Instantiation Orders ("get" operation)
* to view the Request details

**Network Service Instances** 

In this section is possible:
* to retrieve a list of Service instances
* to update an instance to the latest service version

## License

The SONATA BSS is published under Apache 2.0 license. Please see the LICENSE file for more details.

## Useful Links

* [Grunt] (http://gruntjs.com/) - JavaScript Task Runner
* [AngularJS] (https://www.angularjs.org/) - JavaScript Framework for Web apps
* [Bower] (http://bower.io/) - Package manager for the web
* [npm] (https://www.npmjs.com/) -  Package manager for JavaScript
* [node.js] (https://nodejs.org/en/) - JavaScript Runtime 

---
#### Lead Developers

The following lead developers are responsible for this repository and have admin rights. They can, for example, merge pull requests.

 * Santiago Rodriguez (srodriguezOPT)
 * Felipe Vicens (felipevicens)

#### Feedback-Chanel

* You may use the mailing list sonata-dev@lists.atosresearch.eu
* Please use the GitHub issues to report bugs.
