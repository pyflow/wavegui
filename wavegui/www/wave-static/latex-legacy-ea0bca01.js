!function(){function e(e){return function(e){if(Array.isArray(e))return n(e)}(e)||function(e){if("undefined"!=typeof Symbol&&null!=e[Symbol.iterator]||null!=e["@@iterator"])return Array.from(e)}(e)||function(e,a){if(!e)return;if("string"==typeof e)return n(e,a);var t=Object.prototype.toString.call(e).slice(8,-1);"Object"===t&&e.constructor&&(t=e.constructor.name);if("Map"===t||"Set"===t)return Array.from(e);if("Arguments"===t||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t))return n(e,a)}(e)||function(){throw new TypeError("Invalid attempt to spread non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.")}()}function n(e,n){(null==n||n>e.length)&&(n=e.length);for(var a=0,t=new Array(n);a<n;a++)t[a]=e[a];return t}System.register([],(function(n,a){"use strict";return{execute:function(){n("default",(function(n){var a,t=n.regex,r=t.either.apply(t,e(["(?:NeedsTeXFormat|RequirePackage|GetIdInfo)","Provides(?:Expl)?(?:Package|Class|File)","(?:DeclareOption|ProcessOptions)","(?:documentclass|usepackage|input|include)","makeat(?:letter|other)","ExplSyntax(?:On|Off)","(?:new|renew|provide)?command","(?:re)newenvironment","(?:New|Renew|Provide|Declare)(?:Expandable)?DocumentCommand","(?:New|Renew|Provide|Declare)DocumentEnvironment","(?:(?:e|g|x)?def|let)","(?:begin|end)","(?:part|chapter|(?:sub){0,2}section|(?:sub)?paragraph)","caption","(?:label|(?:eq|page|name)?ref|(?:paren|foot|super)?cite)","(?:alpha|beta|[Gg]amma|[Dd]elta|(?:var)?epsilon|zeta|eta|[Tt]heta|vartheta)","(?:iota|(?:var)?kappa|[Ll]ambda|mu|nu|[Xx]i|[Pp]i|varpi|(?:var)rho)","(?:[Ss]igma|varsigma|tau|[Uu]psilon|[Pp]hi|varphi|chi|[Pp]si|[Oo]mega)","(?:frac|sum|prod|lim|infty|times|sqrt|leq|geq|left|right|middle|[bB]igg?)","(?:[lr]angle|q?quad|[lcvdi]?dots|d?dot|hat|tilde|bar)"].map((function(e){return e+"(?![a-zA-Z@:_])"})))),i=new RegExp(["(?:__)?[a-zA-Z]{2,}_[a-zA-Z](?:_?[a-zA-Z])+:[a-zA-Z]*","[lgc]__?[a-zA-Z](?:_?[a-zA-Z])*_[a-zA-Z]{2,}","[qs]__?[a-zA-Z](?:_?[a-zA-Z])+","use(?:_i)?:[a-zA-Z]*","(?:else|fi|or):","(?:if|cs|exp):w","(?:hbox|vbox):n","::[a-zA-Z]_unbraced","::[a-zA-Z:]"].map((function(e){return e+"(?![a-zA-Z:_])"})).join("|")),o=[{begin:/\^{6}[0-9a-f]{6}/},{begin:/\^{5}[0-9a-f]{5}/},{begin:/\^{4}[0-9a-f]{4}/},{begin:/\^{3}[0-9a-f]{3}/},{begin:/\^{2}[0-9a-f]{2}/},{begin:/\^{2}[\u0000-\u007f]/}],c={className:"keyword",begin:/\\/,relevance:0,contains:[{endsParent:!0,begin:r},{endsParent:!0,begin:i},{endsParent:!0,variants:o},{endsParent:!0,relevance:0,variants:[{begin:/[a-zA-Z@]+/},{begin:/[^a-zA-Z@]?/}]}]},s={variants:o},l=n.COMMENT("%","$",{relevance:0}),u=[c,{className:"params",relevance:0,begin:/#+\d?/},s,{className:"built_in",relevance:0,begin:/[$&^_]/},{className:"meta",begin:/% ?!(T[eE]X|tex|BIB|bib)/,end:"$",relevance:10},l],d={begin:/\{/,end:/\}/,relevance:0,contains:["self"].concat(u)},m=n.inherit(d,{relevance:0,endsParent:!0,contains:[d].concat(u)}),f={begin:/\[/,end:/\]/,endsParent:!0,relevance:0,contains:[d].concat(u)},g={begin:/\s+/,relevance:0},b=[m],p=[f],v=function(e,n){return{contains:[g],starts:{relevance:0,contains:e,starts:n}}},A=function(e,n){return{begin:"\\\\"+e+"(?![a-zA-Z@:_])",keywords:{$pattern:/\\[a-zA-Z]+/,keyword:"\\"+e},relevance:0,contains:[g],starts:n}},h=function(e,a){return n.inherit({begin:"\\\\begin(?=[ \t]*(\\r?\\n[ \t]*)?\\{"+e+"\\})",keywords:{$pattern:/\\[a-zA-Z]+/,keyword:"\\begin"},relevance:0},v(b,a))},y=function(){var e=arguments.length>0&&void 0!==arguments[0]?arguments[0]:"string";return n.END_SAME_AS_BEGIN({className:e,begin:/(.|\r?\n)/,end:/(.|\r?\n)/,excludeBegin:!0,excludeEnd:!0,endsParent:!0})},_=function(e){return{className:"string",end:"(?=\\\\end\\{"+e+"\\})"}},z=function(){var e=arguments.length>0&&void 0!==arguments[0]?arguments[0]:"string";return{relevance:0,begin:/\{/,starts:{endsParent:!0,contains:[{className:e,end:/(?=\})/,endsParent:!0,contains:[{begin:/\{/,end:/\}/,relevance:0,contains:["self"]}]}]}}},Z=[].concat(e(["verb","lstinline"].map((function(e){return A(e,{contains:[y()]})}))),[A("mint",v(b,{contains:[y()]})),A("mintinline",v(b,{contains:[z(),y()]})),A("url",{contains:[z("link"),z("link")]}),A("hyperref",{contains:[z("link")]}),A("href",v(p,{contains:[z("link")]}))],e((a=[]).concat.apply(a,e(["","\\*"].map((function(n){return[h("verbatim"+n,_("verbatim"+n)),h("filecontents"+n,v(b,_("filecontents"+n)))].concat(e(["","B","L"].map((function(e){return h(e+"Verbatim"+n,v(p,_(e+"Verbatim"+n)))}))))}))))),[h("minted",v(p,v(b,_("minted"))))]);return{name:"LaTeX",aliases:["tex"],contains:[].concat(e(Z),u)}}))}}}))}();
