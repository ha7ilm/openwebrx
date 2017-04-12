/*
This file is part of libcsdr.

	Copyright (c) Andras Retzler, HA7ILM <randras@sdr.hu>
	Copyright (c) Warren Pratt, NR0V <warren@wpratt.com>
	Copyright 2006,2010,2012 Free Software Foundation, Inc.

    libcsdr is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    libcsdr is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with libcsdr.  If not, see <http://www.gnu.org/licenses/>.
*/

// ========================================================== 
// ========= THE CODE COMPILED BY EMCC STARTS HERE: =========
// ========================================================== 

// Note: For maximum-speed code, see "Optimizing Code" on the Emscripten wiki, https://github.com/kripken/emscripten/wiki/Optimizing-Code
// Note: Some Emscripten settings may limit the speed of the generated code.
// The Module object: Our interface to the outside world. We import
// and export values on it, and do the work to get that through
// closure compiler if necessary. There are various ways Module can be used:
// 1. Not defined. We create it here
// 2. A function parameter, function(Module) { ..generated code.. }
// 3. pre-run appended it, var Module = {}; ..generated code..
// 4. External script tag defines var Module.
// We need to do an eval in order to handle the closure compiler
// case, where this code here is minified but Module was defined
// elsewhere (e.g. case 4 above). We also need to check if Module
// already exists (e.g. case 3 above).
// Note that if you want to run closure, and also to use Module
// after the generated code, you will need to define   var Module = {};
// before the code. Then that object will be used in the code, and you
// can continue to use Module afterwards as well.
var Module;
if (!Module) Module = eval('(function() { try { return Module || {} } catch(e) { return {} } })()');

// Sometimes an existing Module object exists with properties
// meant to overwrite the default module functionality. Here
// we collect those properties and reapply _after_ we configure
// the current environment's defaults to avoid having to be so
// defensive during initialization.
var moduleOverrides = {};
for (var key in Module) {
    if (Module.hasOwnProperty(key)) {
        moduleOverrides[key] = Module[key];
    }
}

// The environment setup code below is customized to use Module.
// *** Environment setup code ***
var ENVIRONMENT_IS_NODE = typeof process === 'object' && typeof require === 'function';
var ENVIRONMENT_IS_WEB = typeof window === 'object';
var ENVIRONMENT_IS_WORKER = typeof importScripts === 'function';
var ENVIRONMENT_IS_SHELL = !ENVIRONMENT_IS_WEB && !ENVIRONMENT_IS_NODE && !ENVIRONMENT_IS_WORKER;

if (ENVIRONMENT_IS_NODE) {
    // Expose functionality in the same simple way that the shells work
    // Note that we pollute the global namespace here, otherwise we break in node
    if (!Module['print']) Module['print'] = function print(x) {
        process['stdout'].write(x + '\n');
    };
    if (!Module['printErr']) Module['printErr'] = function printErr(x) {
        process['stderr'].write(x + '\n');
    };

    var nodeFS = require('fs');
    var nodePath = require('path');

    Module['read'] = function read(filename, binary) {
        filename = nodePath['normalize'](filename);
        var ret = nodeFS['readFileSync'](filename);
        // The path is absolute if the normalized version is the same as the resolved.
        if (!ret && filename != nodePath['resolve'](filename)) {
            filename = path.join(__dirname, '..', 'src', filename);
            ret = nodeFS['readFileSync'](filename);
        }
        if (ret && !binary) ret = ret.toString();
        return ret;
    };

    Module['readBinary'] = function readBinary(filename) {
        return Module['read'](filename, true)
    };

    Module['load'] = function load(f) {
        globalEval(read(f));
    };

    Module['arguments'] = process['argv'].slice(2);

    module['exports'] = Module;
} else if (ENVIRONMENT_IS_SHELL) {
    if (!Module['print']) Module['print'] = print;
    if (typeof printErr != 'undefined') Module['printErr'] = printErr; // not present in v8 or older sm

    if (typeof read != 'undefined') {
        Module['read'] = read;
    } else {
        Module['read'] = function read() {
            throw 'no read() available (jsc?)'
        };
    }

    Module['readBinary'] = function readBinary(f) {
        return read(f, 'binary');
    };

    if (typeof scriptArgs != 'undefined') {
        Module['arguments'] = scriptArgs;
    } else if (typeof arguments != 'undefined') {
        Module['arguments'] = arguments;
    }

    this['Module'] = Module;

    eval("if (typeof gc === 'function' && gc.toString().indexOf('[native code]') > 0) var gc = undefined"); // wipe out the SpiderMonkey shell 'gc' function, which can confuse closure (uses it as a minified name, and it is then initted to a non-falsey value unexpectedly)
} else if (ENVIRONMENT_IS_WEB || ENVIRONMENT_IS_WORKER) {
    Module['read'] = function read(url) {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', url, false);
        xhr.send(null);
        return xhr.responseText;
    };

    if (typeof arguments != 'undefined') {
        Module['arguments'] = arguments;
    }

    if (typeof console !== 'undefined') {
        if (!Module['print']) Module['print'] = function print(x) {
            console.log(x);
        };
        if (!Module['printErr']) Module['printErr'] = function printErr(x) {
            console.log(x);
        };
    } else {
        // Probably a worker, and without console.log. We can do very little here...
        var TRY_USE_DUMP = false;
        if (!Module['print']) Module['print'] = (TRY_USE_DUMP && (typeof(dump) !== "undefined") ? (function(x) {
            dump(x);
        }) : (function(x) {
            // self.postMessage(x); // enable this if you want stdout to be sent as messages
        }));
    }

    if (ENVIRONMENT_IS_WEB) {
        this['Module'] = Module;
    } else {
        Module['load'] = importScripts;
    }
} else {
    // Unreachable because SHELL is dependant on the others
    throw 'Unknown runtime environment. Where are we?';
}

function globalEval(x) {
    eval.call(null, x);
}
if (!Module['load'] == 'undefined' && Module['read']) {
    Module['load'] = function load(f) {
        globalEval(Module['read'](f));
    };
}
if (!Module['print']) {
    Module['print'] = function() {};
}
if (!Module['printErr']) {
    Module['printErr'] = Module['print'];
}
if (!Module['arguments']) {
    Module['arguments'] = [];
}
// *** Environment setup code ***

// Closure helpers
Module.print = Module['print'];
Module.printErr = Module['printErr'];

// Callbacks
Module['preRun'] = [];
Module['postRun'] = [];

// Merge back in the overrides
for (var key in moduleOverrides) {
    if (moduleOverrides.hasOwnProperty(key)) {
        Module[key] = moduleOverrides[key];
    }
}



// === Auto-generated preamble library stuff ===

//========================================
// Runtime code shared with compiler
//========================================

var Runtime = {
    stackSave: function() {
        return STACKTOP;
    },
    stackRestore: function(stackTop) {
        STACKTOP = stackTop;
    },
    forceAlign: function(target, quantum) {
        quantum = quantum || 4;
        if (quantum == 1) return target;
        if (isNumber(target) && isNumber(quantum)) {
            return Math.ceil(target / quantum) * quantum;
        } else if (isNumber(quantum) && isPowerOfTwo(quantum)) {
            return '(((' + target + ')+' + (quantum - 1) + ')&' + -quantum + ')';
        }
        return 'Math.ceil((' + target + ')/' + quantum + ')*' + quantum;
    },
    isNumberType: function(type) {
        return type in Runtime.INT_TYPES || type in Runtime.FLOAT_TYPES;
    },
    isPointerType: function isPointerType(type) {
        return type[type.length - 1] == '*';
    },
    isStructType: function isStructType(type) {
        if (isPointerType(type)) return false;
        if (isArrayType(type)) return true;
        if (/<?{ ?[^}]* ?}>?/.test(type)) return true; // { i32, i8 } etc. - anonymous struct types
        // See comment in isStructPointerType()
        return type[0] == '%';
    },
    INT_TYPES: {
        "i1": 0,
        "i8": 0,
        "i16": 0,
        "i32": 0,
        "i64": 0
    },
    FLOAT_TYPES: {
        "float": 0,
        "double": 0
    },
    or64: function(x, y) {
        var l = (x | 0) | (y | 0);
        var h = (Math.round(x / 4294967296) | Math.round(y / 4294967296)) * 4294967296;
        return l + h;
    },
    and64: function(x, y) {
        var l = (x | 0) & (y | 0);
        var h = (Math.round(x / 4294967296) & Math.round(y / 4294967296)) * 4294967296;
        return l + h;
    },
    xor64: function(x, y) {
        var l = (x | 0) ^ (y | 0);
        var h = (Math.round(x / 4294967296) ^ Math.round(y / 4294967296)) * 4294967296;
        return l + h;
    },
    getNativeTypeSize: function(type) {
        switch (type) {
            case 'i1':
            case 'i8':
                return 1;
            case 'i16':
                return 2;
            case 'i32':
                return 4;
            case 'i64':
                return 8;
            case 'float':
                return 4;
            case 'double':
                return 8;
            default:
                {
                    if (type[type.length - 1] === '*') {
                        return Runtime.QUANTUM_SIZE; // A pointer
                    } else if (type[0] === 'i') {
                        var bits = parseInt(type.substr(1));
                        assert(bits % 8 === 0);
                        return bits / 8;
                    } else {
                        return 0;
                    }
                }
        }
    },
    getNativeFieldSize: function(type) {
        return Math.max(Runtime.getNativeTypeSize(type), Runtime.QUANTUM_SIZE);
    },
    dedup: function dedup(items, ident) {
        var seen = {};
        if (ident) {
            return items.filter(function(item) {
                if (seen[item[ident]]) return false;
                seen[item[ident]] = true;
                return true;
            });
        } else {
            return items.filter(function(item) {
                if (seen[item]) return false;
                seen[item] = true;
                return true;
            });
        }
    },
    set: function set() {
        var args = typeof arguments[0] === 'object' ? arguments[0] : arguments;
        var ret = {};
        for (var i = 0; i < args.length; i++) {
            ret[args[i]] = 0;
        }
        return ret;
    },
    STACK_ALIGN: 8,
    getAlignSize: function(type, size, vararg) {
        // we align i64s and doubles on 64-bit boundaries, unlike x86
        if (vararg) return 8;
        if (!vararg && (type == 'i64' || type == 'double')) return 8;
        if (!type) return Math.min(size, 8); // align structures internally to 64 bits
        return Math.min(size || (type ? Runtime.getNativeFieldSize(type) : 0), Runtime.QUANTUM_SIZE);
    },
    calculateStructAlignment: function calculateStructAlignment(type) {
        type.flatSize = 0;
        type.alignSize = 0;
        var diffs = [];
        var prev = -1;
        var index = 0;
        type.flatIndexes = type.fields.map(function(field) {
            index++;
            var size, alignSize;
            if (Runtime.isNumberType(field) || Runtime.isPointerType(field)) {
                size = Runtime.getNativeTypeSize(field); // pack char; char; in structs, also char[X]s.
                alignSize = Runtime.getAlignSize(field, size);
            } else if (Runtime.isStructType(field)) {
                if (field[1] === '0') {
                    // this is [0 x something]. When inside another structure like here, it must be at the end,
                    // and it adds no size
                    // XXX this happens in java-nbody for example... assert(index === type.fields.length, 'zero-length in the middle!');
                    size = 0;
                    if (Types.types[field]) {
                        alignSize = Runtime.getAlignSize(null, Types.types[field].alignSize);
                    } else {
                        alignSize = type.alignSize || QUANTUM_SIZE;
                    }
                } else {
                    size = Types.types[field].flatSize;
                    alignSize = Runtime.getAlignSize(null, Types.types[field].alignSize);
                }
            } else if (field[0] == 'b') {
                // bN, large number field, like a [N x i8]
                size = field.substr(1) | 0;
                alignSize = 1;
            } else if (field[0] === '<') {
                // vector type
                size = alignSize = Types.types[field].flatSize; // fully aligned
            } else if (field[0] === 'i') {
                // illegal integer field, that could not be legalized because it is an internal structure field
                // it is ok to have such fields, if we just use them as markers of field size and nothing more complex
                size = alignSize = parseInt(field.substr(1)) / 8;
                assert(size % 1 === 0, 'cannot handle non-byte-size field ' + field);
            } else {
                assert(false, 'invalid type for calculateStructAlignment');
            }
            if (type.packed) alignSize = 1;
            type.alignSize = Math.max(type.alignSize, alignSize);
            var curr = Runtime.alignMemory(type.flatSize, alignSize); // if necessary, place this on aligned memory
            type.flatSize = curr + size;
            if (prev >= 0) {
                diffs.push(curr - prev);
            }
            prev = curr;
            return curr;
        });
        if (type.name_ && type.name_[0] === '[') {
            // arrays have 2 elements, so we get the proper difference. then we scale here. that way we avoid
            // allocating a potentially huge array for [999999 x i8] etc.
            type.flatSize = parseInt(type.name_.substr(1)) * type.flatSize / 2;
        }
        type.flatSize = Runtime.alignMemory(type.flatSize, type.alignSize);
        if (diffs.length == 0) {
            type.flatFactor = type.flatSize;
        } else if (Runtime.dedup(diffs).length == 1) {
            type.flatFactor = diffs[0];
        }
        type.needsFlattening = (type.flatFactor != 1);
        return type.flatIndexes;
    },
    generateStructInfo: function(struct, typeName, offset) {
        var type, alignment;
        if (typeName) {
            offset = offset || 0;
            type = (typeof Types === 'undefined' ? Runtime.typeInfo : Types.types)[typeName];
            if (!type) return null;
            if (type.fields.length != struct.length) {
                printErr('Number of named fields must match the type for ' + typeName + ': possibly duplicate struct names. Cannot return structInfo');
                return null;
            }
            alignment = type.flatIndexes;
        } else {
            var type = {
                fields: struct.map(function(item) {
                    return item[0]
                })
            };
            alignment = Runtime.calculateStructAlignment(type);
        }
        var ret = {
            __size__: type.flatSize
        };
        if (typeName) {
            struct.forEach(function(item, i) {
                if (typeof item === 'string') {
                    ret[item] = alignment[i] + offset;
                } else {
                    // embedded struct
                    var key;
                    for (var k in item) key = k;
                    ret[key] = Runtime.generateStructInfo(item[key], type.fields[i], alignment[i]);
                }
            });
        } else {
            struct.forEach(function(item, i) {
                ret[item[1]] = alignment[i];
            });
        }
        return ret;
    },
    dynCall: function(sig, ptr, args) {
        if (args && args.length) {
            if (!args.splice) args = Array.prototype.slice.call(args);
            args.splice(0, 0, ptr);
            return Module['dynCall_' + sig].apply(null, args);
        } else {
            return Module['dynCall_' + sig].call(null, ptr);
        }
    },
    functionPointers: [],
    addFunction: function(func) {
        for (var i = 0; i < Runtime.functionPointers.length; i++) {
            if (!Runtime.functionPointers[i]) {
                Runtime.functionPointers[i] = func;
                return 2 * (1 + i);
            }
        }
        throw 'Finished up all reserved function pointers. Use a higher value for RESERVED_FUNCTION_POINTERS.';
    },
    removeFunction: function(index) {
        Runtime.functionPointers[(index - 2) / 2] = null;
    },
    getAsmConst: function(code, numArgs) {
        // code is a constant string on the heap, so we can cache these
        if (!Runtime.asmConstCache) Runtime.asmConstCache = {};
        var func = Runtime.asmConstCache[code];
        if (func) return func;
        var args = [];
        for (var i = 0; i < numArgs; i++) {
            args.push(String.fromCharCode(36) + i); // $0, $1 etc
        }
        code = Pointer_stringify(code);
        if (code[0] === '"') {
            // tolerate EM_ASM("..code..") even though EM_ASM(..code..) is correct
            if (code.indexOf('"', 1) === code.length - 1) {
                code = code.substr(1, code.length - 2);
            } else {
                // something invalid happened, e.g. EM_ASM("..code($0)..", input)
                abort('invalid EM_ASM input |' + code + '|. Please use EM_ASM(..code..) (no quotes) or EM_ASM({ ..code($0).. }, input) (to input values)');
            }
        }
        return Runtime.asmConstCache[code] = eval('(function(' + args.join(',') + '){ ' + code + ' })'); // new Function does not allow upvars in node
    },
    warnOnce: function(text) {
        if (!Runtime.warnOnce.shown) Runtime.warnOnce.shown = {};
        if (!Runtime.warnOnce.shown[text]) {
            Runtime.warnOnce.shown[text] = 1;
            Module.printErr(text);
        }
    },
    funcWrappers: {},
    getFuncWrapper: function(func, sig) {
        assert(sig);
        if (!Runtime.funcWrappers[func]) {
            Runtime.funcWrappers[func] = function dynCall_wrapper() {
                return Runtime.dynCall(sig, func, arguments);
            };
        }
        return Runtime.funcWrappers[func];
    },
    UTF8Processor: function() {
        var buffer = [];
        var needed = 0;
        this.processCChar = function(code) {
            code = code & 0xFF;

            if (buffer.length == 0) {
                if ((code & 0x80) == 0x00) { // 0xxxxxxx
                    return String.fromCharCode(code);
                }
                buffer.push(code);
                if ((code & 0xE0) == 0xC0) { // 110xxxxx
                    needed = 1;
                } else if ((code & 0xF0) == 0xE0) { // 1110xxxx
                    needed = 2;
                } else { // 11110xxx
                    needed = 3;
                }
                return '';
            }

            if (needed) {
                buffer.push(code);
                needed--;
                if (needed > 0) return '';
            }

            var c1 = buffer[0];
            var c2 = buffer[1];
            var c3 = buffer[2];
            var c4 = buffer[3];
            var ret;
            if (buffer.length == 2) {
                ret = String.fromCharCode(((c1 & 0x1F) << 6) | (c2 & 0x3F));
            } else if (buffer.length == 3) {
                ret = String.fromCharCode(((c1 & 0x0F) << 12) | ((c2 & 0x3F) << 6) | (c3 & 0x3F));
            } else {
                // http://mathiasbynens.be/notes/javascript-encoding#surrogate-formulae
                var codePoint = ((c1 & 0x07) << 18) | ((c2 & 0x3F) << 12) |
                    ((c3 & 0x3F) << 6) | (c4 & 0x3F);
                ret = String.fromCharCode(
                    Math.floor((codePoint - 0x10000) / 0x400) + 0xD800, (codePoint - 0x10000) % 0x400 + 0xDC00);
            }
            buffer.length = 0;
            return ret;
        }
        this.processJSString = function processJSString(string) {
            string = unescape(encodeURIComponent(string));
            var ret = [];
            for (var i = 0; i < string.length; i++) {
                ret.push(string.charCodeAt(i));
            }
            return ret;
        }
    },
    stackAlloc: function(size) {
        var ret = STACKTOP;
        STACKTOP = (STACKTOP + size) | 0;
        STACKTOP = (((STACKTOP) + 7) & -8);
        return ret;
    },
    staticAlloc: function(size) {
        var ret = STATICTOP;
        STATICTOP = (STATICTOP + size) | 0;
        STATICTOP = (((STATICTOP) + 7) & -8);
        return ret;
    },
    dynamicAlloc: function(size) {
        var ret = DYNAMICTOP;
        DYNAMICTOP = (DYNAMICTOP + size) | 0;
        DYNAMICTOP = (((DYNAMICTOP) + 7) & -8);
        if (DYNAMICTOP >= TOTAL_MEMORY) enlargeMemory();;
        return ret;
    },
    alignMemory: function(size, quantum) {
        var ret = size = Math.ceil((size) / (quantum ? quantum : 8)) * (quantum ? quantum : 8);
        return ret;
    },
    makeBigInt: function(low, high, unsigned) {
        var ret = (unsigned ? ((+((low >>> 0))) + ((+((high >>> 0))) * (+4294967296))) : ((+((low >>> 0))) + ((+((high | 0))) * (+4294967296))));
        return ret;
    },
    GLOBAL_BASE: 8,
    QUANTUM_SIZE: 4,
    __dummy__: 0
}


Module['Runtime'] = Runtime;









//========================================
// Runtime essentials
//========================================

var __THREW__ = 0; // Used in checking for thrown exceptions.

var ABORT = false; // whether we are quitting the application. no code should run after this. set in exit() and abort()
var EXITSTATUS = 0;

var undef = 0;
// tempInt is used for 32-bit signed values or smaller. tempBigInt is used
// for 32-bit unsigned values or more than 32 bits. TODO: audit all uses of tempInt
var tempValue, tempInt, tempBigInt, tempInt2, tempBigInt2, tempPair, tempBigIntI, tempBigIntR, tempBigIntS, tempBigIntP, tempBigIntD, tempDouble, tempFloat;
var tempI64, tempI64b;
var tempRet0, tempRet1, tempRet2, tempRet3, tempRet4, tempRet5, tempRet6, tempRet7, tempRet8, tempRet9;

function assert(condition, text) {
    if (!condition) {
        abort('Assertion failed: ' + text);
    }
}

var globalScope = this;

// C calling interface. A convenient way to call C functions (in C files, or
// defined with extern "C").
//
// Note: LLVM optimizations can inline and remove functions, after which you will not be
//       able to call them. Closure can also do so. To avoid that, add your function to
//       the exports using something like
//
//         -s EXPORTED_FUNCTIONS='["_main", "_myfunc"]'
//
// @param ident      The name of the C function (note that C++ functions will be name-mangled - use extern "C")
// @param returnType The return type of the function, one of the JS types 'number', 'string' or 'array' (use 'number' for any C pointer, and
//                   'array' for JavaScript arrays and typed arrays; note that arrays are 8-bit).
// @param argTypes   An array of the types of arguments for the function (if there are no arguments, this can be ommitted). Types are as in returnType,
//                   except that 'array' is not possible (there is no way for us to know the length of the array)
// @param args       An array of the arguments to the function, as native JS values (as in returnType)
//                   Note that string arguments will be stored on the stack (the JS string will become a C string on the stack).
// @return           The return value, as a native JS value (as in returnType)
function ccall(ident, returnType, argTypes, args) {
    return ccallFunc(getCFunc(ident), returnType, argTypes, args);
}
Module["ccall"] = ccall;

// Returns the C function with a specified identifier (for C++, you need to do manual name mangling)
function getCFunc(ident) {
    try {
        var func = Module['_' + ident]; // closure exported function
        if (!func) func = eval('_' + ident); // explicit lookup
    } catch (e) {}
    assert(func, 'Cannot call unknown function ' + ident + ' (perhaps LLVM optimizations or closure removed it?)');
    return func;
}

// Internal function that does a C call using a function, not an identifier
function ccallFunc(func, returnType, argTypes, args) {
    var stack = 0;

    function toC(value, type) {
        if (type == 'string') {
            if (value === null || value === undefined || value === 0) return 0; // null string
            value = intArrayFromString(value);
            type = 'array';
        }
        if (type == 'array') {
            if (!stack) stack = Runtime.stackSave();
            var ret = Runtime.stackAlloc(value.length);
            writeArrayToMemory(value, ret);
            return ret;
        }
        return value;
    }

    function fromC(value, type) {
        if (type == 'string') {
            return Pointer_stringify(value);
        }
        assert(type != 'array');
        return value;
    }
    var i = 0;
    var cArgs = args ? args.map(function(arg) {
        return toC(arg, argTypes[i++]);
    }) : [];
    var ret = fromC(func.apply(null, cArgs), returnType);
    if (stack) Runtime.stackRestore(stack);
    return ret;
}

// Returns a native JS wrapper for a C function. This is similar to ccall, but
// returns a function you can call repeatedly in a normal way. For example:
//
//   var my_function = cwrap('my_c_function', 'number', ['number', 'number']);
//   alert(my_function(5, 22));
//   alert(my_function(99, 12));
//
function cwrap(ident, returnType, argTypes) {
    var func = getCFunc(ident);
    return function() {
        return ccallFunc(func, returnType, argTypes, Array.prototype.slice.call(arguments));
    }
}
Module["cwrap"] = cwrap;

// Sets a value in memory in a dynamic way at run-time. Uses the
// type data. This is the same as makeSetValue, except that
// makeSetValue is done at compile-time and generates the needed
// code then, whereas this function picks the right code at
// run-time.
// Note that setValue and getValue only do *aligned* writes and reads!
// Note that ccall uses JS types as for defining types, while setValue and
// getValue need LLVM types ('i8', 'i32') - this is a lower-level operation
function setValue(ptr, value, type, noSafe) {
    type = type || 'i8';
    if (type.charAt(type.length - 1) === '*') type = 'i32'; // pointers are 32-bit
    switch (type) {
        case 'i1':
            HEAP8[(ptr)] = value;
            break;
        case 'i8':
            HEAP8[(ptr)] = value;
            break;
        case 'i16':
            HEAP16[((ptr) >> 1)] = value;
            break;
        case 'i32':
            HEAP32[((ptr) >> 2)] = value;
            break;
        case 'i64':
            (tempI64 = [value >>> 0, (tempDouble = value, (+(Math_abs(tempDouble))) >= (+1) ? (tempDouble > (+0) ? ((Math_min((+(Math_floor((tempDouble) / (+4294967296)))), (+4294967295))) | 0) >>> 0 : (~~((+(Math_ceil((tempDouble - +(((~~(tempDouble))) >>> 0)) / (+4294967296)))))) >>> 0) : 0)], HEAP32[((ptr) >> 2)] = tempI64[0], HEAP32[(((ptr) + (4)) >> 2)] = tempI64[1]);
            break;
        case 'float':
            HEAPF32[((ptr) >> 2)] = value;
            break;
        case 'double':
            HEAPF64[((ptr) >> 3)] = value;
            break;
        default:
            abort('invalid type for setValue: ' + type);
    }
}
Module['setValue'] = setValue;

// Parallel to setValue.
function getValue(ptr, type, noSafe) {
    type = type || 'i8';
    if (type.charAt(type.length - 1) === '*') type = 'i32'; // pointers are 32-bit
    switch (type) {
        case 'i1':
            return HEAP8[(ptr)];
        case 'i8':
            return HEAP8[(ptr)];
        case 'i16':
            return HEAP16[((ptr) >> 1)];
        case 'i32':
            return HEAP32[((ptr) >> 2)];
        case 'i64':
            return HEAP32[((ptr) >> 2)];
        case 'float':
            return HEAPF32[((ptr) >> 2)];
        case 'double':
            return HEAPF64[((ptr) >> 3)];
        default:
            abort('invalid type for setValue: ' + type);
    }
    return null;
}
Module['getValue'] = getValue;

var ALLOC_NORMAL = 0; // Tries to use _malloc()
var ALLOC_STACK = 1; // Lives for the duration of the current function call
var ALLOC_STATIC = 2; // Cannot be freed
var ALLOC_DYNAMIC = 3; // Cannot be freed except through sbrk
var ALLOC_NONE = 4; // Do not allocate
Module['ALLOC_NORMAL'] = ALLOC_NORMAL;
Module['ALLOC_STACK'] = ALLOC_STACK;
Module['ALLOC_STATIC'] = ALLOC_STATIC;
Module['ALLOC_DYNAMIC'] = ALLOC_DYNAMIC;
Module['ALLOC_NONE'] = ALLOC_NONE;

// allocate(): This is for internal use. You can use it yourself as well, but the interface
//             is a little tricky (see docs right below). The reason is that it is optimized
//             for multiple syntaxes to save space in generated code. So you should
//             normally not use allocate(), and instead allocate memory using _malloc(),
//             initialize it with setValue(), and so forth.
// @slab: An array of data, or a number. If a number, then the size of the block to allocate,
//        in *bytes* (note that this is sometimes confusing: the next parameter does not
//        affect this!)
// @types: Either an array of types, one for each byte (or 0 if no type at that position),
//         or a single type which is used for the entire block. This only matters if there
//         is initial data - if @slab is a number, then this does not matter at all and is
//         ignored.
// @allocator: How to allocate memory, see ALLOC_*
function allocate(slab, types, allocator, ptr) {
    var zeroinit, size;
    if (typeof slab === 'number') {
        zeroinit = true;
        size = slab;
    } else {
        zeroinit = false;
        size = slab.length;
    }

    var singleType = typeof types === 'string' ? types : null;

    var ret;
    if (allocator == ALLOC_NONE) {
        ret = ptr;
    } else {
        ret = [_malloc, Runtime.stackAlloc, Runtime.staticAlloc, Runtime.dynamicAlloc][allocator === undefined ? ALLOC_STATIC : allocator](Math.max(size, singleType ? 1 : types.length));
    }

    if (zeroinit) {
        var ptr = ret,
            stop;
        assert((ret & 3) == 0);
        stop = ret + (size & ~3);
        for (; ptr < stop; ptr += 4) {
            HEAP32[((ptr) >> 2)] = 0;
        }
        stop = ret + size;
        while (ptr < stop) {
            HEAP8[((ptr++) | 0)] = 0;
        }
        return ret;
    }

    if (singleType === 'i8') {
        if (slab.subarray || slab.slice) {
            HEAPU8.set(slab, ret);
        } else {
            HEAPU8.set(new Uint8Array(slab), ret);
        }
        return ret;
    }

    var i = 0,
        type, typeSize, previousType;
    while (i < size) {
        var curr = slab[i];

        if (typeof curr === 'function') {
            curr = Runtime.getFunctionIndex(curr);
        }

        type = singleType || types[i];
        if (type === 0) {
            i++;
            continue;
        }

        if (type == 'i64') type = 'i32'; // special case: we have one i32 here, and one i32 later

        setValue(ret + i, curr, type);

        // no need to look up size unless type changes, so cache it
        if (previousType !== type) {
            typeSize = Runtime.getNativeTypeSize(type);
            previousType = type;
        }
        i += typeSize;
    }

    return ret;
}
Module['allocate'] = allocate;

function Pointer_stringify(ptr, /* optional */ length) {
    // TODO: use TextDecoder
    // Find the length, and check for UTF while doing so
    var hasUtf = false;
    var t;
    var i = 0;
    while (1) {
        t = HEAPU8[(((ptr) + (i)) | 0)];
        if (t >= 128) hasUtf = true;
        else if (t == 0 && !length) break;
        i++;
        if (length && i == length) break;
    }
    if (!length) length = i;

    var ret = '';

    if (!hasUtf) {
        var MAX_CHUNK = 1024; // split up into chunks, because .apply on a huge string can overflow the stack
        var curr;
        while (length > 0) {
            curr = String.fromCharCode.apply(String, HEAPU8.subarray(ptr, ptr + Math.min(length, MAX_CHUNK)));
            ret = ret ? ret + curr : curr;
            ptr += MAX_CHUNK;
            length -= MAX_CHUNK;
        }
        return ret;
    }

    var utf8 = new Runtime.UTF8Processor();
    for (i = 0; i < length; i++) {
        t = HEAPU8[(((ptr) + (i)) | 0)];
        ret += utf8.processCChar(t);
    }
    return ret;
}
Module['Pointer_stringify'] = Pointer_stringify;

// Given a pointer 'ptr' to a null-terminated UTF16LE-encoded string in the emscripten HEAP, returns
// a copy of that string as a Javascript String object.
function UTF16ToString(ptr) {
    var i = 0;

    var str = '';
    while (1) {
        var codeUnit = HEAP16[(((ptr) + (i * 2)) >> 1)];
        if (codeUnit == 0)
            return str;
        ++i;
        // fromCharCode constructs a character from a UTF-16 code unit, so we can pass the UTF16 string right through.
        str += String.fromCharCode(codeUnit);
    }
}
Module['UTF16ToString'] = UTF16ToString;

// Copies the given Javascript String object 'str' to the emscripten HEAP at address 'outPtr',
// null-terminated and encoded in UTF16LE form. The copy will require at most (str.length*2+1)*2 bytes of space in the HEAP.
function stringToUTF16(str, outPtr) {
    for (var i = 0; i < str.length; ++i) {
        // charCodeAt returns a UTF-16 encoded code unit, so it can be directly written to the HEAP.
        var codeUnit = str.charCodeAt(i); // possibly a lead surrogate
        HEAP16[(((outPtr) + (i * 2)) >> 1)] = codeUnit;
    }
    // Null-terminate the pointer to the HEAP.
    HEAP16[(((outPtr) + (str.length * 2)) >> 1)] = 0;
}
Module['stringToUTF16'] = stringToUTF16;

// Given a pointer 'ptr' to a null-terminated UTF32LE-encoded string in the emscripten HEAP, returns
// a copy of that string as a Javascript String object.
function UTF32ToString(ptr) {
    var i = 0;

    var str = '';
    while (1) {
        var utf32 = HEAP32[(((ptr) + (i * 4)) >> 2)];
        if (utf32 == 0)
            return str;
        ++i;
        // Gotcha: fromCharCode constructs a character from a UTF-16 encoded code (pair), not from a Unicode code point! So encode the code point to UTF-16 for constructing.
        if (utf32 >= 0x10000) {
            var ch = utf32 - 0x10000;
            str += String.fromCharCode(0xD800 | (ch >> 10), 0xDC00 | (ch & 0x3FF));
        } else {
            str += String.fromCharCode(utf32);
        }
    }
}
Module['UTF32ToString'] = UTF32ToString;

// Copies the given Javascript String object 'str' to the emscripten HEAP at address 'outPtr',
// null-terminated and encoded in UTF32LE form. The copy will require at most (str.length+1)*4 bytes of space in the HEAP,
// but can use less, since str.length does not return the number of characters in the string, but the number of UTF-16 code units in the string.
function stringToUTF32(str, outPtr) {
    var iChar = 0;
    for (var iCodeUnit = 0; iCodeUnit < str.length; ++iCodeUnit) {
        // Gotcha: charCodeAt returns a 16-bit word that is a UTF-16 encoded code unit, not a Unicode code point of the character! We must decode the string to UTF-32 to the heap.
        var codeUnit = str.charCodeAt(iCodeUnit); // possibly a lead surrogate
        if (codeUnit >= 0xD800 && codeUnit <= 0xDFFF) {
            var trailSurrogate = str.charCodeAt(++iCodeUnit);
            codeUnit = 0x10000 + ((codeUnit & 0x3FF) << 10) | (trailSurrogate & 0x3FF);
        }
        HEAP32[(((outPtr) + (iChar * 4)) >> 2)] = codeUnit;
        ++iChar;
    }
    // Null-terminate the pointer to the HEAP.
    HEAP32[(((outPtr) + (iChar * 4)) >> 2)] = 0;
}
Module['stringToUTF32'] = stringToUTF32;

function demangle(func) {
    try {
        // Special-case the entry point, since its name differs from other name mangling.
        if (func == 'Object._main' || func == '_main') {
            return 'main()';
        }
        if (typeof func === 'number') func = Pointer_stringify(func);
        if (func[0] !== '_') return func;
        if (func[1] !== '_') return func; // C function
        if (func[2] !== 'Z') return func;
        switch (func[3]) {
            case 'n':
                return 'operator new()';
            case 'd':
                return 'operator delete()';
        }
        var i = 3;
        // params, etc.
        var basicTypes = {
            'v': 'void',
            'b': 'bool',
            'c': 'char',
            's': 'short',
            'i': 'int',
            'l': 'long',
            'f': 'float',
            'd': 'double',
            'w': 'wchar_t',
            'a': 'signed char',
            'h': 'unsigned char',
            't': 'unsigned short',
            'j': 'unsigned int',
            'm': 'unsigned long',
            'x': 'long long',
            'y': 'unsigned long long',
            'z': '...'
        };

        function dump(x) {
            //return;
            if (x) Module.print(x);
            Module.print(func);
            var pre = '';
            for (var a = 0; a < i; a++) pre += ' ';
            Module.print(pre + '^');
        }
        var subs = [];

        function parseNested() {
            i++;
            if (func[i] === 'K') i++; // ignore const
            var parts = [];
            while (func[i] !== 'E') {
                if (func[i] === 'S') { // substitution
                    i++;
                    var next = func.indexOf('_', i);
                    var num = func.substring(i, next) || 0;
                    parts.push(subs[num] || '?');
                    i = next + 1;
                    continue;
                }
                if (func[i] === 'C') { // constructor
                    parts.push(parts[parts.length - 1]);
                    i += 2;
                    continue;
                }
                var size = parseInt(func.substr(i));
                var pre = size.toString().length;
                if (!size || !pre) {
                    i--;
                    break;
                } // counter i++ below us
                var curr = func.substr(i + pre, size);
                parts.push(curr);
                subs.push(curr);
                i += pre + size;
            }
            i++; // skip E
            return parts;
        }
        var first = true;

        function parse(rawList, limit, allowVoid) { // main parser
            limit = limit || Infinity;
            var ret = '',
                list = [];

            function flushList() {
                return '(' + list.join(', ') + ')';
            }
            var name;
            if (func[i] === 'N') {
                // namespaced N-E
                name = parseNested().join('::');
                limit--;
                if (limit === 0) return rawList ? [name] : name;
            } else {
                // not namespaced
                if (func[i] === 'K' || (first && func[i] === 'L')) i++; // ignore const and first 'L'
                var size = parseInt(func.substr(i));
                if (size) {
                    var pre = size.toString().length;
                    name = func.substr(i + pre, size);
                    i += pre + size;
                }
            }
            first = false;
            if (func[i] === 'I') {
                i++;
                var iList = parse(true);
                var iRet = parse(true, 1, true);
                ret += iRet[0] + ' ' + name + '<' + iList.join(', ') + '>';
            } else {
                ret = name;
            }
            paramLoop: while (i < func.length && limit-- > 0) {
                //dump('paramLoop');
                var c = func[i++];
                if (c in basicTypes) {
                    list.push(basicTypes[c]);
                } else {
                    switch (c) {
                        case 'P':
                            list.push(parse(true, 1, true)[0] + '*');
                            break; // pointer
                        case 'R':
                            list.push(parse(true, 1, true)[0] + '&');
                            break; // reference
                        case 'L':
                            { // literal
                                i++; // skip basic type
                                var end = func.indexOf('E', i);
                                var size = end - i;
                                list.push(func.substr(i, size));
                                i += size + 2; // size + 'EE'
                                break;
                            }
                        case 'A':
                            { // array
                                var size = parseInt(func.substr(i));
                                i += size.toString().length;
                                if (func[i] !== '_') throw '?';
                                i++; // skip _
                                list.push(parse(true, 1, true)[0] + ' [' + size + ']');
                                break;
                            }
                        case 'E':
                            break paramLoop;
                        default:
                            ret += '?' + c;
                            break paramLoop;
                    }
                }
            }
            if (!allowVoid && list.length === 1 && list[0] === 'void') list = []; // avoid (void)
            return rawList ? list : ret + flushList();
        }
        return parse();
    } catch (e) {
        return func;
    }
}

function demangleAll(text) {
    return text.replace(/__Z[\w\d_]+/g, function(x) {
        var y = demangle(x);
        return x === y ? x : (x + ' [' + y + ']')
    });
}

function stackTrace() {
    var stack = new Error().stack;
    return stack ? demangleAll(stack) : '(no stack trace available)'; // Stack trace is not available at least on IE10 and Safari 6.
}

// Memory management

var PAGE_SIZE = 4096;

function alignMemoryPage(x) {
    return (x + 4095) & -4096;
}

var HEAP;
var HEAP8, HEAPU8, HEAP16, HEAPU16, HEAP32, HEAPU32, HEAPF32, HEAPF64;

var STATIC_BASE = 0,
    STATICTOP = 0,
    staticSealed = false; // static area
var STACK_BASE = 0,
    STACKTOP = 0,
    STACK_MAX = 0; // stack area
var DYNAMIC_BASE = 0,
    DYNAMICTOP = 0; // dynamic area handled by sbrk

function enlargeMemory() {
    abort('Cannot enlarge memory arrays in asm.js. Either (1) compile with -s TOTAL_MEMORY=X with X higher than the current value ' + TOTAL_MEMORY + ', or (2) set Module.TOTAL_MEMORY before the program runs.');
}

var TOTAL_STACK = Module['TOTAL_STACK'] || 5242880;
var TOTAL_MEMORY = Module['TOTAL_MEMORY'] || 67108864;
var FAST_MEMORY = Module['FAST_MEMORY'] || 2097152;

var totalMemory = 4096;
while (totalMemory < TOTAL_MEMORY || totalMemory < 2 * TOTAL_STACK) {
    if (totalMemory < 16 * 1024 * 1024) {
        totalMemory *= 2;
    } else {
        totalMemory += 16 * 1024 * 1024
    }
}
if (totalMemory !== TOTAL_MEMORY) {
    Module.printErr('increasing TOTAL_MEMORY to ' + totalMemory + ' to be more reasonable');
    TOTAL_MEMORY = totalMemory;
}

// Initialize the runtime's memory
// check for full engine support (use string 'subarray' to avoid closure compiler confusion)
assert(typeof Int32Array !== 'undefined' && typeof Float64Array !== 'undefined' && !!(new Int32Array(1)['subarray']) && !!(new Int32Array(1)['set']),
    'Cannot fallback to non-typed array case: Code is too specialized');

var buffer = new ArrayBuffer(TOTAL_MEMORY);
HEAP8 = new Int8Array(buffer);
HEAP16 = new Int16Array(buffer);
HEAP32 = new Int32Array(buffer);
HEAPU8 = new Uint8Array(buffer);
HEAPU16 = new Uint16Array(buffer);
HEAPU32 = new Uint32Array(buffer);
HEAPF32 = new Float32Array(buffer);
HEAPF64 = new Float64Array(buffer);

// Endianness check (note: assumes compiler arch was little-endian)
HEAP32[0] = 255;
assert(HEAPU8[0] === 255 && HEAPU8[3] === 0, 'Typed arrays 2 must be run on a little-endian system');

Module['HEAP'] = HEAP;
Module['HEAP8'] = HEAP8;
Module['HEAP16'] = HEAP16;
Module['HEAP32'] = HEAP32;
Module['HEAPU8'] = HEAPU8;
Module['HEAPU16'] = HEAPU16;
Module['HEAPU32'] = HEAPU32;
Module['HEAPF32'] = HEAPF32;
Module['HEAPF64'] = HEAPF64;

function callRuntimeCallbacks(callbacks) {
    while (callbacks.length > 0) {
        var callback = callbacks.shift();
        if (typeof callback == 'function') {
            callback();
            continue;
        }
        var func = callback.func;
        if (typeof func === 'number') {
            if (callback.arg === undefined) {
                Runtime.dynCall('v', func);
            } else {
                Runtime.dynCall('vi', func, [callback.arg]);
            }
        } else {
            func(callback.arg === undefined ? null : callback.arg);
        }
    }
}

var __ATPRERUN__ = []; // functions called before the runtime is initialized
var __ATINIT__ = []; // functions called during startup
var __ATMAIN__ = []; // functions called when main() is to be run
var __ATEXIT__ = []; // functions called during shutdown
var __ATPOSTRUN__ = []; // functions called after the runtime has exited

var runtimeInitialized = false;

function preRun() {
    // compatibility - merge in anything from Module['preRun'] at this time
    if (Module['preRun']) {
        if (typeof Module['preRun'] == 'function') Module['preRun'] = [Module['preRun']];
        while (Module['preRun'].length) {
            addOnPreRun(Module['preRun'].shift());
        }
    }
    callRuntimeCallbacks(__ATPRERUN__);
}

function ensureInitRuntime() {
    if (runtimeInitialized) return;
    runtimeInitialized = true;
    callRuntimeCallbacks(__ATINIT__);
}

function preMain() {
    callRuntimeCallbacks(__ATMAIN__);
}

function exitRuntime() {
    callRuntimeCallbacks(__ATEXIT__);
}

function postRun() {
    // compatibility - merge in anything from Module['postRun'] at this time
    if (Module['postRun']) {
        if (typeof Module['postRun'] == 'function') Module['postRun'] = [Module['postRun']];
        while (Module['postRun'].length) {
            addOnPostRun(Module['postRun'].shift());
        }
    }
    callRuntimeCallbacks(__ATPOSTRUN__);
}

function addOnPreRun(cb) {
    __ATPRERUN__.unshift(cb);
}
Module['addOnPreRun'] = Module.addOnPreRun = addOnPreRun;

function addOnInit(cb) {
    __ATINIT__.unshift(cb);
}
Module['addOnInit'] = Module.addOnInit = addOnInit;

function addOnPreMain(cb) {
    __ATMAIN__.unshift(cb);
}
Module['addOnPreMain'] = Module.addOnPreMain = addOnPreMain;

function addOnExit(cb) {
    __ATEXIT__.unshift(cb);
}
Module['addOnExit'] = Module.addOnExit = addOnExit;

function addOnPostRun(cb) {
    __ATPOSTRUN__.unshift(cb);
}
Module['addOnPostRun'] = Module.addOnPostRun = addOnPostRun;

// Tools

// This processes a JS string into a C-line array of numbers, 0-terminated.
// For LLVM-originating strings, see parser.js:parseLLVMString function
function intArrayFromString(stringy, dontAddNull, length /* optional */ ) {
    var ret = (new Runtime.UTF8Processor()).processJSString(stringy);
    if (length) {
        ret.length = length;
    }
    if (!dontAddNull) {
        ret.push(0);
    }
    return ret;
}
Module['intArrayFromString'] = intArrayFromString;

function intArrayToString(array) {
    var ret = [];
    for (var i = 0; i < array.length; i++) {
        var chr = array[i];
        if (chr > 0xFF) {
            chr &= 0xFF;
        }
        ret.push(String.fromCharCode(chr));
    }
    return ret.join('');
}
Module['intArrayToString'] = intArrayToString;

// Write a Javascript array to somewhere in the heap
function writeStringToMemory(string, buffer, dontAddNull) {
    var array = intArrayFromString(string, dontAddNull);
    var i = 0;
    while (i < array.length) {
        var chr = array[i];
        HEAP8[(((buffer) + (i)) | 0)] = chr;
        i = i + 1;
    }
}
Module['writeStringToMemory'] = writeStringToMemory;

function writeArrayToMemory(array, buffer) {
    for (var i = 0; i < array.length; i++) {
        HEAP8[(((buffer) + (i)) | 0)] = array[i];
    }
}
Module['writeArrayToMemory'] = writeArrayToMemory;

function writeAsciiToMemory(str, buffer, dontAddNull) {
    for (var i = 0; i < str.length; i++) {
        HEAP8[(((buffer) + (i)) | 0)] = str.charCodeAt(i);
    }
    if (!dontAddNull) HEAP8[(((buffer) + (str.length)) | 0)] = 0;
}
Module['writeAsciiToMemory'] = writeAsciiToMemory;

function unSign(value, bits, ignore, sig) {
    if (value >= 0) {
        return value;
    }
    return bits <= 32 ? 2 * Math.abs(1 << (bits - 1)) + value // Need some trickery, since if bits == 32, we are right at the limit of the bits JS uses in bitshifts
        : Math.pow(2, bits) + value;
}

function reSign(value, bits, ignore, sig) {
    if (value <= 0) {
        return value;
    }
    var half = bits <= 32 ? Math.abs(1 << (bits - 1)) // abs is needed if bits == 32
        : Math.pow(2, bits - 1);
    if (value >= half && (bits <= 32 || value > half)) { // for huge values, we can hit the precision limit and always get true here. so don't do that
        // but, in general there is no perfect solution here. With 64-bit ints, we get rounding and errors
        // TODO: In i64 mode 1, resign the two parts separately and safely
        value = -2 * half + value; // Cannot bitshift half, as it may be at the limit of the bits JS uses in bitshifts
    }
    return value;
}

// check for imul support, and also for correctness ( https://bugs.webkit.org/show_bug.cgi?id=126345 )
if (!Math['imul'] || Math['imul'](0xffffffff, 5) !== -5) Math['imul'] = function imul(a, b) {
    var ah = a >>> 16;
    var al = a & 0xffff;
    var bh = b >>> 16;
    var bl = b & 0xffff;
    return (al * bl + ((ah * bl + al * bh) << 16)) | 0;
};
Math.imul = Math['imul'];


var Math_abs = Math.abs;
var Math_cos = Math.cos;
var Math_sin = Math.sin;
var Math_tan = Math.tan;
var Math_acos = Math.acos;
var Math_asin = Math.asin;
var Math_atan = Math.atan;
var Math_atan2 = Math.atan2;
var Math_exp = Math.exp;
var Math_log = Math.log;
var Math_sqrt = Math.sqrt;
var Math_ceil = Math.ceil;
var Math_floor = Math.floor;
var Math_pow = Math.pow;
var Math_imul = Math.imul;
var Math_fround = Math.fround;
var Math_min = Math.min;

// A counter of dependencies for calling run(). If we need to
// do asynchronous work before running, increment this and
// decrement it. Incrementing must happen in a place like
// PRE_RUN_ADDITIONS (used by emcc to add file preloading).
// Note that you can add dependencies in preRun, even though
// it happens right before run - run will be postponed until
// the dependencies are met.
var runDependencies = 0;
var runDependencyWatcher = null;
var dependenciesFulfilled = null; // overridden to take different actions when all run dependencies are fulfilled

function addRunDependency(id) {
    runDependencies++;
    if (Module['monitorRunDependencies']) {
        Module['monitorRunDependencies'](runDependencies);
    }
}
Module['addRunDependency'] = addRunDependency;

function removeRunDependency(id) {
    runDependencies--;
    if (Module['monitorRunDependencies']) {
        Module['monitorRunDependencies'](runDependencies);
    }
    if (runDependencies == 0) {
        if (runDependencyWatcher !== null) {
            clearInterval(runDependencyWatcher);
            runDependencyWatcher = null;
        }
        if (dependenciesFulfilled) {
            var callback = dependenciesFulfilled;
            dependenciesFulfilled = null;
            callback(); // can add another dependenciesFulfilled
        }
    }
}
Module['removeRunDependency'] = removeRunDependency;

Module["preloadedImages"] = {}; // maps url to image data
Module["preloadedAudios"] = {}; // maps url to audio data


var memoryInitializer = null;

// === Body ===



STATIC_BASE = 8;

STATICTOP = STATIC_BASE + 3016;


/* global initializers */
__ATINIT__.push({
    func: function() {
        runPostSets()
    }
});









/* memory initializer */
allocate([93, 59, 32, 101, 114, 114, 111, 114, 95, 118, 101, 99, 116, 111, 114, 95, 100, 98, 61, 50, 48, 42, 108, 111, 103, 49, 48, 40, 101, 114, 114, 111, 114, 95, 118, 101, 99, 116, 111, 114, 41, 59, 32, 112, 108, 111, 116, 40, 101, 114, 114, 111, 114, 95, 118, 101, 99, 116, 111, 114, 95, 100, 98, 41, 59, 0, 0, 0, 0, 0, 0, 0, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 2, 0, 0, 0, 4, 0, 0, 0, 6, 0, 0, 0, 8, 0, 0, 0, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 2, 0, 0, 0, 4, 0, 0, 0, 6, 0, 0, 0, 8, 0, 0, 0, 28, 231, 5, 82, 18, 219, 7, 82, 171, 207, 217, 210, 255, 248, 185, 81, 67, 26, 172, 211, 92, 100, 176, 210, 167, 29, 24, 212, 1, 58, 121, 211, 5, 161, 70, 212, 42, 210, 182, 211, 240, 134, 66, 212, 116, 10, 164, 211, 11, 46, 229, 211, 37, 173, 82, 210, 45, 128, 69, 83, 130, 129, 238, 83, 100, 212, 139, 84, 33, 133, 147, 84, 14, 87, 4, 85, 54, 41, 234, 84, 49, 183, 53, 85, 74, 117, 15, 85, 185, 20, 69, 85, 219, 25, 7, 85, 149, 8, 31, 85, 184, 136, 154, 84, 234, 77, 91, 84, 128, 81, 20, 212, 1, 159, 234, 212, 243, 146, 75, 213, 95, 236, 172, 213, 100, 44, 202, 213, 103, 156, 23, 214, 63, 161, 23, 214, 128, 90, 88, 214, 221, 79, 60, 214, 252, 178, 135, 214, 115, 177, 41, 214, 73, 44, 154, 214, 136, 253, 9, 87, 166, 141, 226, 87, 136, 253, 9, 87, 73, 44, 154, 214, 115, 177, 41, 214, 252, 178, 135, 214, 221, 79, 60, 214, 128, 90, 88, 214, 63, 161, 23, 214, 103, 156, 23, 214, 100, 44, 202, 213, 95, 236, 172, 213, 243, 146, 75, 213, 1, 159, 234, 212, 128, 81, 20, 212, 234, 77, 91, 84, 184, 136, 154, 84, 149, 8, 31, 85, 219, 25, 7, 85, 185, 20, 69, 85, 74, 117, 15, 85, 49, 183, 53, 85, 54, 41, 234, 84, 14, 87, 4, 85, 33, 133, 147, 84, 100, 212, 139, 84, 130, 129, 238, 83, 45, 128, 69, 83, 37, 173, 82, 210, 11, 46, 229, 211, 116, 10, 164, 211, 240, 134, 66, 212, 42, 210, 182, 211, 5, 161, 70, 212, 1, 58, 121, 211, 167, 29, 24, 212, 92, 100, 176, 210, 67, 26, 172, 211, 255, 248, 185, 81, 171, 207, 217, 210, 18, 219, 7, 82, 28, 231, 5, 82, 0, 0, 0, 0, 54, 48, 226, 58, 146, 125, 235, 58, 103, 152, 251, 58, 165, 142, 6, 59, 225, 4, 13, 59, 38, 144, 14, 59, 103, 147, 9, 59, 60, 177, 251, 58, 143, 77, 217, 58, 50, 249, 176, 58, 123, 7, 137, 58, 54, 86, 79, 58, 190, 7, 35, 58, 95, 252, 16, 58, 171, 157, 22, 58, 247, 87, 43, 58, 110, 118, 66, 58, 80, 3, 78, 58, 177, 6, 66, 58, 198, 99, 23, 58, 147, 77, 155, 57, 198, 133, 165, 184, 132, 132, 3, 186, 86, 199, 111, 186, 31, 120, 165, 186, 168, 52, 197, 186, 109, 19, 213, 186, 217, 231, 214, 186, 70, 11, 208, 186, 187, 54, 200, 186, 74, 193, 199, 186, 29, 174, 213, 186, 147, 247, 245, 186, 236, 65, 20, 187, 171, 131, 52, 187, 237, 240, 87, 187, 225, 230, 121, 187, 227, 255, 138, 187, 218, 143, 148, 187, 201, 29, 153, 187, 231, 85, 153, 187, 170, 248, 150, 187, 96, 122, 148, 187, 24, 117, 148, 187, 20, 11, 153, 187, 107, 95, 163, 187, 189, 69, 179, 187, 0, 61, 199, 187, 238, 187, 220, 187, 239, 190, 240, 187, 7, 61, 0, 188, 20, 3, 5, 188, 230, 111, 6, 188, 36, 12, 5, 188, 23, 20, 2, 188, 105, 106, 254, 187, 152, 89, 252, 187, 126, 93, 0, 188, 67, 116, 6, 188, 95, 51, 16, 188, 124, 114, 28, 188, 166, 86, 41, 188, 110, 184, 52, 188, 55, 165, 60, 188, 201, 216, 63, 188, 23, 26, 62, 188, 211, 92, 56, 188, 128, 156, 48, 188, 176, 117, 41, 188, 179, 144, 37, 188, 23, 251, 38, 188, 236, 150, 46, 188, 20, 198, 59, 188, 142, 104, 76, 188, 167, 54, 93, 188, 133, 108, 106, 188, 9, 168, 112, 188, 66, 198, 109, 188, 112, 148, 97, 188, 171, 26, 78, 188, 2, 111, 55, 188, 184, 1, 35, 188, 168, 120, 22, 188, 132, 80, 22, 188, 167, 127, 36, 188, 179, 102, 63, 188, 133, 85, 97, 188, 50, 99, 128, 188, 123, 181, 136, 188, 142, 242, 130, 188, 68, 247, 81, 188, 44, 158, 217, 187, 212, 209, 51, 59, 70, 233, 119, 60, 3, 184, 244, 60, 154, 24, 60, 61, 16, 180, 125, 61, 88, 146, 156, 61, 151, 75, 180, 61, 17, 154, 195, 61, 239, 227, 200, 61, 17, 154, 195, 61, 151, 75, 180, 61, 88, 146, 156, 61, 16, 180, 125, 61, 154, 24, 60, 61, 3, 184, 244, 60, 70, 233, 119, 60, 212, 209, 51, 59, 44, 158, 217, 187, 68, 247, 81, 188, 142, 242, 130, 188, 123, 181, 136, 188, 50, 99, 128, 188, 133, 85, 97, 188, 179, 102, 63, 188, 167, 127, 36, 188, 132, 80, 22, 188, 168, 120, 22, 188, 184, 1, 35, 188, 2, 111, 55, 188, 171, 26, 78, 188, 112, 148, 97, 188, 66, 198, 109, 188, 9, 168, 112, 188, 133, 108, 106, 188, 167, 54, 93, 188, 142, 104, 76, 188, 20, 198, 59, 188, 236, 150, 46, 188, 23, 251, 38, 188, 179, 144, 37, 188, 176, 117, 41, 188, 128, 156, 48, 188, 211, 92, 56, 188, 23, 26, 62, 188, 201, 216, 63, 188, 55, 165, 60, 188, 110, 184, 52, 188, 166, 86, 41, 188, 124, 114, 28, 188, 95, 51, 16, 188, 67, 116, 6, 188, 126, 93, 0, 188, 152, 89, 252, 187, 105, 106, 254, 187, 23, 20, 2, 188, 36, 12, 5, 188, 230, 111, 6, 188, 20, 3, 5, 188, 7, 61, 0, 188, 239, 190, 240, 187, 238, 187, 220, 187, 0, 61, 199, 187, 189, 69, 179, 187, 107, 95, 163, 187, 20, 11, 153, 187, 24, 117, 148, 187, 96, 122, 148, 187, 170, 248, 150, 187, 231, 85, 153, 187, 201, 29, 153, 187, 218, 143, 148, 187, 227, 255, 138, 187, 225, 230, 121, 187, 237, 240, 87, 187, 171, 131, 52, 187, 236, 65, 20, 187, 147, 247, 245, 186, 29, 174, 213, 186, 74, 193, 199, 186, 187, 54, 200, 186, 70, 11, 208, 186, 217, 231, 214, 186, 109, 19, 213, 186, 168, 52, 197, 186, 31, 120, 165, 186, 86, 199, 111, 186, 132, 132, 3, 186, 198, 133, 165, 184, 147, 77, 155, 57, 198, 99, 23, 58, 177, 6, 66, 58, 80, 3, 78, 58, 110, 118, 66, 58, 247, 87, 43, 58, 171, 157, 22, 58, 95, 252, 16, 58, 190, 7, 35, 58, 54, 86, 79, 58, 123, 7, 137, 58, 50, 249, 176, 58, 143, 77, 217, 58, 60, 177, 251, 58, 103, 147, 9, 59, 38, 144, 14, 59, 225, 4, 13, 59, 165, 142, 6, 59, 103, 152, 251, 58, 146, 125, 235, 58, 54, 48, 226, 58, 0, 0, 0, 0, 31, 224, 36, 59, 115, 56, 74, 59, 230, 137, 111, 59, 29, 135, 135, 59, 153, 60, 146, 59, 19, 29, 151, 59, 62, 4, 151, 59, 69, 68, 148, 59, 76, 15, 146, 59, 251, 153, 147, 59, 121, 52, 155, 59, 235, 152, 169, 59, 141, 162, 189, 59, 195, 136, 212, 59, 91, 146, 234, 59, 58, 21, 252, 59, 198, 63, 3, 60, 242, 143, 4, 60, 97, 184, 2, 60, 227, 203, 254, 59, 231, 145, 249, 59, 66, 250, 249, 59, 117, 110, 1, 60, 62, 101, 10, 60, 189, 221, 22, 60, 202, 186, 36, 60, 103, 75, 49, 60, 223, 4, 58, 60, 104, 64, 61, 60, 141, 196, 58, 60, 184, 243, 51, 60, 134, 137, 43, 60, 246, 237, 36, 60, 48, 73, 35, 60, 173, 144, 40, 60, 29, 212, 52, 60, 174, 2, 70, 60, 249, 67, 88, 60, 174, 220, 102, 60, 136, 113, 109, 60, 5, 86, 105, 60, 111, 144, 90, 60, 153, 59, 68, 60, 58, 26, 44, 60, 222, 86, 25, 60, 242, 163, 18, 60, 23, 35, 28, 60, 236, 141, 53, 60, 193, 31, 89, 60, 81, 164, 123, 60, 139, 228, 134, 60, 66, 159, 126, 60, 247, 221, 62, 60, 52, 158, 136, 59, 157, 147, 230, 187, 33, 62, 176, 188, 194, 133, 28, 189, 27, 184, 99, 189, 141, 28, 147, 189, 179, 58, 174, 189, 76, 247, 191, 189, 169, 34, 198, 189, 76, 247, 191, 189, 179, 58, 174, 189, 141, 28, 147, 189, 27, 184, 99, 189, 194, 133, 28, 189, 33, 62, 176, 188, 157, 147, 230, 187, 52, 158, 136, 59, 247, 221, 62, 60, 66, 159, 126, 60, 139, 228, 134, 60, 81, 164, 123, 60, 193, 31, 89, 60, 236, 141, 53, 60, 23, 35, 28, 60, 242, 163, 18, 60, 222, 86, 25, 60, 58, 26, 44, 60, 153, 59, 68, 60, 111, 144, 90, 60, 5, 86, 105, 60, 136, 113, 109, 60, 174, 220, 102, 60, 249, 67, 88, 60, 174, 2, 70, 60, 29, 212, 52, 60, 173, 144, 40, 60, 48, 73, 35, 60, 246, 237, 36, 60, 134, 137, 43, 60, 184, 243, 51, 60, 141, 196, 58, 60, 104, 64, 61, 60, 223, 4, 58, 60, 103, 75, 49, 60, 202, 186, 36, 60, 189, 221, 22, 60, 62, 101, 10, 60, 117, 110, 1, 60, 66, 250, 249, 59, 231, 145, 249, 59, 227, 203, 254, 59, 97, 184, 2, 60, 242, 143, 4, 60, 198, 63, 3, 60, 58, 21, 252, 59, 91, 146, 234, 59, 195, 136, 212, 59, 141, 162, 189, 59, 235, 152, 169, 59, 121, 52, 155, 59, 251, 153, 147, 59, 76, 15, 146, 59, 69, 68, 148, 59, 62, 4, 151, 59, 19, 29, 151, 59, 153, 60, 146, 59, 29, 135, 135, 59, 230, 137, 111, 59, 115, 56, 74, 59, 31, 224, 36, 59, 0, 0, 0, 0, 222, 82, 148, 58, 17, 222, 110, 58, 163, 210, 227, 58, 235, 251, 178, 185, 117, 168, 94, 186, 111, 92, 173, 185, 6, 130, 62, 187, 91, 45, 106, 187, 215, 43, 81, 187, 101, 237, 198, 187, 202, 1, 216, 187, 193, 29, 197, 187, 211, 66, 17, 188, 17, 56, 16, 188, 21, 252, 248, 187, 83, 103, 36, 188, 95, 206, 17, 188, 215, 183, 217, 187, 66, 217, 8, 188, 238, 187, 187, 187, 136, 81, 12, 187, 132, 53, 70, 187, 131, 50, 174, 58, 211, 116, 205, 59, 139, 117, 195, 59, 64, 206, 69, 60, 98, 208, 147, 60, 214, 96, 144, 60, 175, 228, 207, 60, 251, 170, 1, 61, 215, 132, 244, 60, 212, 33, 33, 61, 123, 176, 54, 61, 125, 184, 31, 61, 18, 139, 83, 61, 135, 202, 85, 61, 75, 112, 15, 61, 167, 37, 118, 61, 108, 162, 133, 60, 35, 191, 94, 190, 20, 207, 193, 190, 35, 191, 94, 190, 108, 162, 133, 60, 167, 37, 118, 61, 75, 112, 15, 61, 135, 202, 85, 61, 18, 139, 83, 61, 125, 184, 31, 61, 123, 176, 54, 61, 212, 33, 33, 61, 215, 132, 244, 60, 251, 170, 1, 61, 175, 228, 207, 60, 214, 96, 144, 60, 98, 208, 147, 60, 64, 206, 69, 60, 139, 117, 195, 59, 211, 116, 205, 59, 131, 50, 174, 58, 132, 53, 70, 187, 136, 81, 12, 187, 238, 187, 187, 187, 66, 217, 8, 188, 215, 183, 217, 187, 95, 206, 17, 188, 83, 103, 36, 188, 21, 252, 248, 187, 17, 56, 16, 188, 211, 66, 17, 188, 193, 29, 197, 187, 202, 1, 216, 187, 101, 237, 198, 187, 215, 43, 81, 187, 91, 45, 106, 187, 6, 130, 62, 187, 111, 92, 173, 185, 117, 168, 94, 186, 235, 251, 178, 185, 163, 210, 227, 58, 17, 222, 110, 58, 222, 82, 148, 58, 0, 0, 0, 0, 37, 103, 32, 0, 0, 0, 0, 0, 101, 114, 114, 111, 114, 95, 118, 101, 99, 116, 111, 114, 61, 91, 0, 0, 73, 78, 86, 65, 76, 73, 68, 0, 72, 65, 77, 77, 73, 78, 71, 0, 66, 76, 65, 67, 75, 77, 65, 78, 0, 0, 0, 0, 0, 0, 0, 0, 66, 79, 88, 67, 65, 82, 0, 0, 7, 0, 0, 0, 8, 0, 0, 0, 9, 0, 0, 0, 10, 0, 0, 0, 11, 0, 0, 0, 12, 0, 0, 0, 13, 0, 0, 0, 14, 0, 0, 0, 16, 0, 0, 0, 17, 0, 0, 0, 19, 0, 0, 0, 21, 0, 0, 0, 23, 0, 0, 0, 25, 0, 0, 0, 28, 0, 0, 0, 31, 0, 0, 0, 34, 0, 0, 0, 37, 0, 0, 0, 41, 0, 0, 0, 45, 0, 0, 0, 50, 0, 0, 0, 55, 0, 0, 0, 60, 0, 0, 0, 66, 0, 0, 0, 73, 0, 0, 0, 80, 0, 0, 0, 88, 0, 0, 0, 97, 0, 0, 0, 107, 0, 0, 0, 118, 0, 0, 0, 130, 0, 0, 0, 143, 0, 0, 0, 157, 0, 0, 0, 173, 0, 0, 0, 190, 0, 0, 0, 209, 0, 0, 0, 230, 0, 0, 0, 253, 0, 0, 0, 23, 1, 0, 0, 51, 1, 0, 0, 81, 1, 0, 0, 115, 1, 0, 0, 152, 1, 0, 0, 193, 1, 0, 0, 238, 1, 0, 0, 32, 2, 0, 0, 86, 2, 0, 0, 146, 2, 0, 0, 212, 2, 0, 0, 28, 3, 0, 0, 108, 3, 0, 0, 195, 3, 0, 0, 36, 4, 0, 0, 142, 4, 0, 0, 2, 5, 0, 0, 131, 5, 0, 0, 16, 6, 0, 0, 171, 6, 0, 0, 86, 7, 0, 0, 18, 8, 0, 0, 224, 8, 0, 0, 195, 9, 0, 0, 189, 10, 0, 0, 208, 11, 0, 0, 255, 12, 0, 0, 76, 14, 0, 0, 186, 15, 0, 0, 76, 17, 0, 0, 7, 19, 0, 0, 238, 20, 0, 0, 6, 23, 0, 0, 84, 25, 0, 0, 220, 27, 0, 0, 165, 30, 0, 0, 182, 33, 0, 0, 21, 37, 0, 0, 202, 40, 0, 0, 223, 44, 0, 0, 91, 49, 0, 0, 75, 54, 0, 0, 185, 59, 0, 0, 178, 65, 0, 0, 68, 72, 0, 0, 126, 79, 0, 0, 113, 87, 0, 0, 47, 96, 0, 0, 206, 105, 0, 0, 98, 116, 0, 0, 255, 127, 0, 0, 0, 0, 0, 0], "i8", ALLOC_NONE, Runtime.GLOBAL_BASE);



var tempDoublePtr = Runtime.alignMemory(allocate(12, "i8", ALLOC_STATIC), 8);

assert(tempDoublePtr % 8 == 0);

function copyTempFloat(ptr) { // functions, because inlining this code increases code size too much

    HEAP8[tempDoublePtr] = HEAP8[ptr];

    HEAP8[tempDoublePtr + 1] = HEAP8[ptr + 1];

    HEAP8[tempDoublePtr + 2] = HEAP8[ptr + 2];

    HEAP8[tempDoublePtr + 3] = HEAP8[ptr + 3];

}

function copyTempDouble(ptr) {

    HEAP8[tempDoublePtr] = HEAP8[ptr];

    HEAP8[tempDoublePtr + 1] = HEAP8[ptr + 1];

    HEAP8[tempDoublePtr + 2] = HEAP8[ptr + 2];

    HEAP8[tempDoublePtr + 3] = HEAP8[ptr + 3];

    HEAP8[tempDoublePtr + 4] = HEAP8[ptr + 4];

    HEAP8[tempDoublePtr + 5] = HEAP8[ptr + 5];

    HEAP8[tempDoublePtr + 6] = HEAP8[ptr + 6];

    HEAP8[tempDoublePtr + 7] = HEAP8[ptr + 7];

}



function _strncmp(px, py, n) {
    var i = 0;
    while (i < n) {
        var x = HEAPU8[(((px) + (i)) | 0)];
        var y = HEAPU8[(((py) + (i)) | 0)];
        if (x == y && x == 0) return 0;
        if (x == 0) return -1;
        if (y == 0) return 1;
        if (x == y) {
            i++;
            continue;
        } else {
            return x > y ? 1 : -1;
        }
    }
    return 0;
}

function _strcmp(px, py) {
    return _strncmp(px, py, TOTAL_MEMORY);
}

var _cos = Math_cos;

var _sin = Math_sin;



Module["_memcpy"] = _memcpy;
var _llvm_memcpy_p0i8_p0i8_i32 = _memcpy;

var _ceilf = Math_ceil;

var _fabs = Math_abs;

var _atan2 = Math_atan2;

function _log10(x) {
    return Math.log(x) / Math.LN10;
}





var ERRNO_CODES = {
    EPERM: 1,
    ENOENT: 2,
    ESRCH: 3,
    EINTR: 4,
    EIO: 5,
    ENXIO: 6,
    E2BIG: 7,
    ENOEXEC: 8,
    EBADF: 9,
    ECHILD: 10,
    EAGAIN: 11,
    EWOULDBLOCK: 11,
    ENOMEM: 12,
    EACCES: 13,
    EFAULT: 14,
    ENOTBLK: 15,
    EBUSY: 16,
    EEXIST: 17,
    EXDEV: 18,
    ENODEV: 19,
    ENOTDIR: 20,
    EISDIR: 21,
    EINVAL: 22,
    ENFILE: 23,
    EMFILE: 24,
    ENOTTY: 25,
    ETXTBSY: 26,
    EFBIG: 27,
    ENOSPC: 28,
    ESPIPE: 29,
    EROFS: 30,
    EMLINK: 31,
    EPIPE: 32,
    EDOM: 33,
    ERANGE: 34,
    ENOMSG: 42,
    EIDRM: 43,
    ECHRNG: 44,
    EL2NSYNC: 45,
    EL3HLT: 46,
    EL3RST: 47,
    ELNRNG: 48,
    EUNATCH: 49,
    ENOCSI: 50,
    EL2HLT: 51,
    EDEADLK: 35,
    ENOLCK: 37,
    EBADE: 52,
    EBADR: 53,
    EXFULL: 54,
    ENOANO: 55,
    EBADRQC: 56,
    EBADSLT: 57,
    EDEADLOCK: 35,
    EBFONT: 59,
    ENOSTR: 60,
    ENODATA: 61,
    ETIME: 62,
    ENOSR: 63,
    ENONET: 64,
    ENOPKG: 65,
    EREMOTE: 66,
    ENOLINK: 67,
    EADV: 68,
    ESRMNT: 69,
    ECOMM: 70,
    EPROTO: 71,
    EMULTIHOP: 72,
    EDOTDOT: 73,
    EBADMSG: 74,
    ENOTUNIQ: 76,
    EBADFD: 77,
    EREMCHG: 78,
    ELIBACC: 79,
    ELIBBAD: 80,
    ELIBSCN: 81,
    ELIBMAX: 82,
    ELIBEXEC: 83,
    ENOSYS: 38,
    ENOTEMPTY: 39,
    ENAMETOOLONG: 36,
    ELOOP: 40,
    EOPNOTSUPP: 95,
    EPFNOSUPPORT: 96,
    ECONNRESET: 104,
    ENOBUFS: 105,
    EAFNOSUPPORT: 97,
    EPROTOTYPE: 91,
    ENOTSOCK: 88,
    ENOPROTOOPT: 92,
    ESHUTDOWN: 108,
    ECONNREFUSED: 111,
    EADDRINUSE: 98,
    ECONNABORTED: 103,
    ENETUNREACH: 101,
    ENETDOWN: 100,
    ETIMEDOUT: 110,
    EHOSTDOWN: 112,
    EHOSTUNREACH: 113,
    EINPROGRESS: 115,
    EALREADY: 114,
    EDESTADDRREQ: 89,
    EMSGSIZE: 90,
    EPROTONOSUPPORT: 93,
    ESOCKTNOSUPPORT: 94,
    EADDRNOTAVAIL: 99,
    ENETRESET: 102,
    EISCONN: 106,
    ENOTCONN: 107,
    ETOOMANYREFS: 109,
    EUSERS: 87,
    EDQUOT: 122,
    ESTALE: 116,
    ENOTSUP: 95,
    ENOMEDIUM: 123,
    EILSEQ: 84,
    EOVERFLOW: 75,
    ECANCELED: 125,
    ENOTRECOVERABLE: 131,
    EOWNERDEAD: 130,
    ESTRPIPE: 86
};

var ERRNO_MESSAGES = {
    0: "Success",
    1: "Not super-user",
    2: "No such file or directory",
    3: "No such process",
    4: "Interrupted system call",
    5: "I/O error",
    6: "No such device or address",
    7: "Arg list too long",
    8: "Exec format error",
    9: "Bad file number",
    10: "No children",
    11: "No more processes",
    12: "Not enough core",
    13: "Permission denied",
    14: "Bad address",
    15: "Block device required",
    16: "Mount device busy",
    17: "File exists",
    18: "Cross-device link",
    19: "No such device",
    20: "Not a directory",
    21: "Is a directory",
    22: "Invalid argument",
    23: "Too many open files in system",
    24: "Too many open files",
    25: "Not a typewriter",
    26: "Text file busy",
    27: "File too large",
    28: "No space left on device",
    29: "Illegal seek",
    30: "Read only file system",
    31: "Too many links",
    32: "Broken pipe",
    33: "Math arg out of domain of func",
    34: "Math result not representable",
    35: "File locking deadlock error",
    36: "File or path name too long",
    37: "No record locks available",
    38: "Function not implemented",
    39: "Directory not empty",
    40: "Too many symbolic links",
    42: "No message of desired type",
    43: "Identifier removed",
    44: "Channel number out of range",
    45: "Level 2 not synchronized",
    46: "Level 3 halted",
    47: "Level 3 reset",
    48: "Link number out of range",
    49: "Protocol driver not attached",
    50: "No CSI structure available",
    51: "Level 2 halted",
    52: "Invalid exchange",
    53: "Invalid request descriptor",
    54: "Exchange full",
    55: "No anode",
    56: "Invalid request code",
    57: "Invalid slot",
    59: "Bad font file fmt",
    60: "Device not a stream",
    61: "No data (for no delay io)",
    62: "Timer expired",
    63: "Out of streams resources",
    64: "Machine is not on the network",
    65: "Package not installed",
    66: "The object is remote",
    67: "The link has been severed",
    68: "Advertise error",
    69: "Srmount error",
    70: "Communication error on send",
    71: "Protocol error",
    72: "Multihop attempted",
    73: "Cross mount point (not really error)",
    74: "Trying to read unreadable message",
    75: "Value too large for defined data type",
    76: "Given log. name not unique",
    77: "f.d. invalid for this operation",
    78: "Remote address changed",
    79: "Can   access a needed shared lib",
    80: "Accessing a corrupted shared lib",
    81: ".lib section in a.out corrupted",
    82: "Attempting to link in too many libs",
    83: "Attempting to exec a shared library",
    84: "Illegal byte sequence",
    86: "Streams pipe error",
    87: "Too many users",
    88: "Socket operation on non-socket",
    89: "Destination address required",
    90: "Message too long",
    91: "Protocol wrong type for socket",
    92: "Protocol not available",
    93: "Unknown protocol",
    94: "Socket type not supported",
    95: "Not supported",
    96: "Protocol family not supported",
    97: "Address family not supported by protocol family",
    98: "Address already in use",
    99: "Address not available",
    100: "Network interface is not configured",
    101: "Network is unreachable",
    102: "Connection reset by network",
    103: "Connection aborted",
    104: "Connection reset by peer",
    105: "No buffer space available",
    106: "Socket is already connected",
    107: "Socket is not connected",
    108: "Can't send after socket shutdown",
    109: "Too many references",
    110: "Connection timed out",
    111: "Connection refused",
    112: "Host is down",
    113: "Host is unreachable",
    114: "Socket already connected",
    115: "Connection already in progress",
    116: "Stale file handle",
    122: "Quota exceeded",
    123: "No medium (in tape drive)",
    125: "Operation canceled",
    130: "Previous owner died",
    131: "State not recoverable"
};


var ___errno_state = 0;

function ___setErrNo(value) {
    // For convenient setting and returning of errno.
    HEAP32[((___errno_state) >> 2)] = value;
    return value;
}

var PATH = {
    splitPath: function(filename) {
        var splitPathRe = /^(\/?|)([\s\S]*?)((?:\.{1,2}|[^\/]+?|)(\.[^.\/]*|))(?:[\/]*)$/;
        return splitPathRe.exec(filename).slice(1);
    },
    normalizeArray: function(parts, allowAboveRoot) {
        // if the path tries to go above the root, `up` ends up > 0
        var up = 0;
        for (var i = parts.length - 1; i >= 0; i--) {
            var last = parts[i];
            if (last === '.') {
                parts.splice(i, 1);
            } else if (last === '..') {
                parts.splice(i, 1);
                up++;
            } else if (up) {
                parts.splice(i, 1);
                up--;
            }
        }
        // if the path is allowed to go above the root, restore leading ..s
        if (allowAboveRoot) {
            for (; up--; up) {
                parts.unshift('..');
            }
        }
        return parts;
    },
    normalize: function(path) {
        var isAbsolute = path.charAt(0) === '/',
            trailingSlash = path.substr(-1) === '/';
        // Normalize the path
        path = PATH.normalizeArray(path.split('/').filter(function(p) {
            return !!p;
        }), !isAbsolute).join('/');
        if (!path && !isAbsolute) {
            path = '.';
        }
        if (path && trailingSlash) {
            path += '/';
        }
        return (isAbsolute ? '/' : '') + path;
    },
    dirname: function(path) {
        var result = PATH.splitPath(path),
            root = result[0],
            dir = result[1];
        if (!root && !dir) {
            // No dirname whatsoever
            return '.';
        }
        if (dir) {
            // It has a dirname, strip trailing slash
            dir = dir.substr(0, dir.length - 1);
        }
        return root + dir;
    },
    basename: function(path) {
        // EMSCRIPTEN return '/'' for '/', not an empty string
        if (path === '/') return '/';
        var lastSlash = path.lastIndexOf('/');
        if (lastSlash === -1) return path;
        return path.substr(lastSlash + 1);
    },
    extname: function(path) {
        return PATH.splitPath(path)[3];
    },
    join: function() {
        var paths = Array.prototype.slice.call(arguments, 0);
        return PATH.normalize(paths.join('/'));
    },
    join2: function(l, r) {
        return PATH.normalize(l + '/' + r);
    },
    resolve: function() {
        var resolvedPath = '',
            resolvedAbsolute = false;
        for (var i = arguments.length - 1; i >= -1 && !resolvedAbsolute; i--) {
            var path = (i >= 0) ? arguments[i] : FS.cwd();
            // Skip empty and invalid entries
            if (typeof path !== 'string') {
                throw new TypeError('Arguments to path.resolve must be strings');
            } else if (!path) {
                continue;
            }
            resolvedPath = path + '/' + resolvedPath;
            resolvedAbsolute = path.charAt(0) === '/';
        }
        // At this point the path should be resolved to a full absolute path, but
        // handle relative paths to be safe (might happen when process.cwd() fails)
        resolvedPath = PATH.normalizeArray(resolvedPath.split('/').filter(function(p) {
            return !!p;
        }), !resolvedAbsolute).join('/');
        return ((resolvedAbsolute ? '/' : '') + resolvedPath) || '.';
    },
    relative: function(from, to) {
        from = PATH.resolve(from).substr(1);
        to = PATH.resolve(to).substr(1);

        function trim(arr) {
            var start = 0;
            for (; start < arr.length; start++) {
                if (arr[start] !== '') break;
            }
            var end = arr.length - 1;
            for (; end >= 0; end--) {
                if (arr[end] !== '') break;
            }
            if (start > end) return [];
            return arr.slice(start, end - start + 1);
        }
        var fromParts = trim(from.split('/'));
        var toParts = trim(to.split('/'));
        var length = Math.min(fromParts.length, toParts.length);
        var samePartsLength = length;
        for (var i = 0; i < length; i++) {
            if (fromParts[i] !== toParts[i]) {
                samePartsLength = i;
                break;
            }
        }
        var outputParts = [];
        for (var i = samePartsLength; i < fromParts.length; i++) {
            outputParts.push('..');
        }
        outputParts = outputParts.concat(toParts.slice(samePartsLength));
        return outputParts.join('/');
    }
};

var TTY = {
    ttys: [],
    init: function() {
        // https://github.com/kripken/emscripten/pull/1555
        // if (ENVIRONMENT_IS_NODE) {
        //   // currently, FS.init does not distinguish if process.stdin is a file or TTY
        //   // device, it always assumes it's a TTY device. because of this, we're forcing
        //   // process.stdin to UTF8 encoding to at least make stdin reading compatible
        //   // with text files until FS.init can be refactored.
        //   process['stdin']['setEncoding']('utf8');
        // }
    },
    shutdown: function() {
        // https://github.com/kripken/emscripten/pull/1555
        // if (ENVIRONMENT_IS_NODE) {
        //   // inolen: any idea as to why node -e 'process.stdin.read()' wouldn't exit immediately (with process.stdin being a tty)?
        //   // isaacs: because now it's reading from the stream, you've expressed interest in it, so that read() kicks off a _read() which creates a ReadReq operation
        //   // inolen: I thought read() in that case was a synchronous operation that just grabbed some amount of buffered data if it exists?
        //   // isaacs: it is. but it also triggers a _read() call, which calls readStart() on the handle
        //   // isaacs: do process.stdin.pause() and i'd think it'd probably close the pending call
        //   process['stdin']['pause']();
        // }
    },
    register: function(dev, ops) {
        TTY.ttys[dev] = {
            input: [],
            output: [],
            ops: ops
        };
        FS.registerDevice(dev, TTY.stream_ops);
    },
    stream_ops: {
        open: function(stream) {
            var tty = TTY.ttys[stream.node.rdev];
            if (!tty) {
                throw new FS.ErrnoError(ERRNO_CODES.ENODEV);
            }
            stream.tty = tty;
            stream.seekable = false;
        },
        close: function(stream) {
            // flush any pending line data
            if (stream.tty.output.length) {
                stream.tty.ops.put_char(stream.tty, 10);
            }
        },
        read: function(stream, buffer, offset, length, pos /* ignored */ ) {
            if (!stream.tty || !stream.tty.ops.get_char) {
                throw new FS.ErrnoError(ERRNO_CODES.ENXIO);
            }
            var bytesRead = 0;
            for (var i = 0; i < length; i++) {
                var result;
                try {
                    result = stream.tty.ops.get_char(stream.tty);
                } catch (e) {
                    throw new FS.ErrnoError(ERRNO_CODES.EIO);
                }
                if (result === undefined && bytesRead === 0) {
                    throw new FS.ErrnoError(ERRNO_CODES.EAGAIN);
                }
                if (result === null || result === undefined) break;
                bytesRead++;
                buffer[offset + i] = result;
            }
            if (bytesRead) {
                stream.node.timestamp = Date.now();
            }
            return bytesRead;
        },
        write: function(stream, buffer, offset, length, pos) {
            if (!stream.tty || !stream.tty.ops.put_char) {
                throw new FS.ErrnoError(ERRNO_CODES.ENXIO);
            }
            for (var i = 0; i < length; i++) {
                try {
                    stream.tty.ops.put_char(stream.tty, buffer[offset + i]);
                } catch (e) {
                    throw new FS.ErrnoError(ERRNO_CODES.EIO);
                }
            }
            if (length) {
                stream.node.timestamp = Date.now();
            }
            return i;
        }
    },
    default_tty_ops: {
        get_char: function(tty) {
            if (!tty.input.length) {
                var result = null;
                if (ENVIRONMENT_IS_NODE) {
                    result = process['stdin']['read']();
                    if (!result) {
                        if (process['stdin']['_readableState'] && process['stdin']['_readableState']['ended']) {
                            return null; // EOF
                        }
                        return undefined; // no data available
                    }
                } else if (typeof window != 'undefined' &&
                    typeof window.prompt == 'function') {
                    // Browser.
                    result = window.prompt('Input: '); // returns null on cancel
                    if (result !== null) {
                        result += '\n';
                    }
                } else if (typeof readline == 'function') {
                    // Command line.
                    result = readline();
                    if (result !== null) {
                        result += '\n';
                    }
                }
                if (!result) {
                    return null;
                }
                tty.input = intArrayFromString(result, true);
            }
            return tty.input.shift();
        },
        put_char: function(tty, val) {
            if (val === null || val === 10) {
                Module['print'](tty.output.join(''));
                tty.output = [];
            } else {
                tty.output.push(TTY.utf8.processCChar(val));
            }
        }
    },
    default_tty1_ops: {
        put_char: function(tty, val) {
            if (val === null || val === 10) {
                Module['printErr'](tty.output.join(''));
                tty.output = [];
            } else {
                tty.output.push(TTY.utf8.processCChar(val));
            }
        }
    }
};

var MEMFS = {
    ops_table: null,
    CONTENT_OWNING: 1,
    CONTENT_FLEXIBLE: 2,
    CONTENT_FIXED: 3,
    mount: function(mount) {
        return MEMFS.createNode(null, '/', 16384 | 0777, 0);
    },
    createNode: function(parent, name, mode, dev) {
        if (FS.isBlkdev(mode) || FS.isFIFO(mode)) {
            // no supported
            throw new FS.ErrnoError(ERRNO_CODES.EPERM);
        }
        if (!MEMFS.ops_table) {
            MEMFS.ops_table = {
                dir: {
                    node: {
                        getattr: MEMFS.node_ops.getattr,
                        setattr: MEMFS.node_ops.setattr,
                        lookup: MEMFS.node_ops.lookup,
                        mknod: MEMFS.node_ops.mknod,
                        mknod: MEMFS.node_ops.mknod,
                        rename: MEMFS.node_ops.rename,
                        unlink: MEMFS.node_ops.unlink,
                        rmdir: MEMFS.node_ops.rmdir,
                        readdir: MEMFS.node_ops.readdir,
                        symlink: MEMFS.node_ops.symlink
                    },
                    stream: {
                        llseek: MEMFS.stream_ops.llseek
                    }
                },
                file: {
                    node: {
                        getattr: MEMFS.node_ops.getattr,
                        setattr: MEMFS.node_ops.setattr
                    },
                    stream: {
                        llseek: MEMFS.stream_ops.llseek,
                        read: MEMFS.stream_ops.read,
                        write: MEMFS.stream_ops.write,
                        allocate: MEMFS.stream_ops.allocate,
                        mmap: MEMFS.stream_ops.mmap
                    }
                },
                link: {
                    node: {
                        getattr: MEMFS.node_ops.getattr,
                        setattr: MEMFS.node_ops.setattr,
                        readlink: MEMFS.node_ops.readlink
                    },
                    stream: {}
                },
                chrdev: {
                    node: {
                        getattr: MEMFS.node_ops.getattr,
                        setattr: MEMFS.node_ops.setattr
                    },
                    stream: FS.chrdev_stream_ops
                },
            };
        }
        var node = FS.createNode(parent, name, mode, dev);
        if (FS.isDir(node.mode)) {
            node.node_ops = MEMFS.ops_table.dir.node;
            node.stream_ops = MEMFS.ops_table.dir.stream;
            node.contents = {};
        } else if (FS.isFile(node.mode)) {
            node.node_ops = MEMFS.ops_table.file.node;
            node.stream_ops = MEMFS.ops_table.file.stream;
            node.contents = [];
            node.contentMode = MEMFS.CONTENT_FLEXIBLE;
        } else if (FS.isLink(node.mode)) {
            node.node_ops = MEMFS.ops_table.link.node;
            node.stream_ops = MEMFS.ops_table.link.stream;
        } else if (FS.isChrdev(node.mode)) {
            node.node_ops = MEMFS.ops_table.chrdev.node;
            node.stream_ops = MEMFS.ops_table.chrdev.stream;
        }
        node.timestamp = Date.now();
        // add the new node to the parent
        if (parent) {
            parent.contents[name] = node;
        }
        return node;
    },
    ensureFlexible: function(node) {
        if (node.contentMode !== MEMFS.CONTENT_FLEXIBLE) {
            var contents = node.contents;
            node.contents = Array.prototype.slice.call(contents);
            node.contentMode = MEMFS.CONTENT_FLEXIBLE;
        }
    },
    node_ops: {
        getattr: function(node) {
            var attr = {};
            // device numbers reuse inode numbers.
            attr.dev = FS.isChrdev(node.mode) ? node.id : 1;
            attr.ino = node.id;
            attr.mode = node.mode;
            attr.nlink = 1;
            attr.uid = 0;
            attr.gid = 0;
            attr.rdev = node.rdev;
            if (FS.isDir(node.mode)) {
                attr.size = 4096;
            } else if (FS.isFile(node.mode)) {
                attr.size = node.contents.length;
            } else if (FS.isLink(node.mode)) {
                attr.size = node.link.length;
            } else {
                attr.size = 0;
            }
            attr.atime = new Date(node.timestamp);
            attr.mtime = new Date(node.timestamp);
            attr.ctime = new Date(node.timestamp);
            // NOTE: In our implementation, st_blocks = Math.ceil(st_size/st_blksize),
            //       but this is not required by the standard.
            attr.blksize = 4096;
            attr.blocks = Math.ceil(attr.size / attr.blksize);
            return attr;
        },
        setattr: function(node, attr) {
            if (attr.mode !== undefined) {
                node.mode = attr.mode;
            }
            if (attr.timestamp !== undefined) {
                node.timestamp = attr.timestamp;
            }
            if (attr.size !== undefined) {
                MEMFS.ensureFlexible(node);
                var contents = node.contents;
                if (attr.size < contents.length) contents.length = attr.size;
                else
                    while (attr.size > contents.length) contents.push(0);
            }
        },
        lookup: function(parent, name) {
            throw FS.genericErrors[ERRNO_CODES.ENOENT];
        },
        mknod: function(parent, name, mode, dev) {
            return MEMFS.createNode(parent, name, mode, dev);
        },
        rename: function(old_node, new_dir, new_name) {
            // if we're overwriting a directory at new_name, make sure it's empty.
            if (FS.isDir(old_node.mode)) {
                var new_node;
                try {
                    new_node = FS.lookupNode(new_dir, new_name);
                } catch (e) {}
                if (new_node) {
                    for (var i in new_node.contents) {
                        throw new FS.ErrnoError(ERRNO_CODES.ENOTEMPTY);
                    }
                }
            }
            // do the internal rewiring
            delete old_node.parent.contents[old_node.name];
            old_node.name = new_name;
            new_dir.contents[new_name] = old_node;
            old_node.parent = new_dir;
        },
        unlink: function(parent, name) {
            delete parent.contents[name];
        },
        rmdir: function(parent, name) {
            var node = FS.lookupNode(parent, name);
            for (var i in node.contents) {
                throw new FS.ErrnoError(ERRNO_CODES.ENOTEMPTY);
            }
            delete parent.contents[name];
        },
        readdir: function(node) {
            var entries = ['.', '..']
            for (var key in node.contents) {
                if (!node.contents.hasOwnProperty(key)) {
                    continue;
                }
                entries.push(key);
            }
            return entries;
        },
        symlink: function(parent, newname, oldpath) {
            var node = MEMFS.createNode(parent, newname, 0777 | 40960, 0);
            node.link = oldpath;
            return node;
        },
        readlink: function(node) {
            if (!FS.isLink(node.mode)) {
                throw new FS.ErrnoError(ERRNO_CODES.EINVAL);
            }
            return node.link;
        }
    },
    stream_ops: {
        read: function(stream, buffer, offset, length, position) {
            var contents = stream.node.contents;
            if (position >= contents.length)
                return 0;
            var size = Math.min(contents.length - position, length);
            assert(size >= 0);
            if (size > 8 && contents.subarray) { // non-trivial, and typed array
                buffer.set(contents.subarray(position, position + size), offset);
            } else {
                for (var i = 0; i < size; i++) {
                    buffer[offset + i] = contents[position + i];
                }
            }
            return size;
        },
        write: function(stream, buffer, offset, length, position, canOwn) {
            var node = stream.node;
            node.timestamp = Date.now();
            var contents = node.contents;
            if (length && contents.length === 0 && position === 0 && buffer.subarray) {
                // just replace it with the new data
                if (canOwn && offset === 0) {
                    node.contents = buffer; // this could be a subarray of Emscripten HEAP, or allocated from some other source.
                    node.contentMode = (buffer.buffer === HEAP8.buffer) ? MEMFS.CONTENT_OWNING : MEMFS.CONTENT_FIXED;
                } else {
                    node.contents = new Uint8Array(buffer.subarray(offset, offset + length));
                    node.contentMode = MEMFS.CONTENT_FIXED;
                }
                return length;
            }
            MEMFS.ensureFlexible(node);
            var contents = node.contents;
            while (contents.length < position) contents.push(0);
            for (var i = 0; i < length; i++) {
                contents[position + i] = buffer[offset + i];
            }
            return length;
        },
        llseek: function(stream, offset, whence) {
            var position = offset;
            if (whence === 1) { // SEEK_CUR.
                position += stream.position;
            } else if (whence === 2) { // SEEK_END.
                if (FS.isFile(stream.node.mode)) {
                    position += stream.node.contents.length;
                }
            }
            if (position < 0) {
                throw new FS.ErrnoError(ERRNO_CODES.EINVAL);
            }
            stream.ungotten = [];
            stream.position = position;
            return position;
        },
        allocate: function(stream, offset, length) {
            MEMFS.ensureFlexible(stream.node);
            var contents = stream.node.contents;
            var limit = offset + length;
            while (limit > contents.length) contents.push(0);
        },
        mmap: function(stream, buffer, offset, length, position, prot, flags) {
            if (!FS.isFile(stream.node.mode)) {
                throw new FS.ErrnoError(ERRNO_CODES.ENODEV);
            }
            var ptr;
            var allocated;
            var contents = stream.node.contents;
            // Only make a new copy when MAP_PRIVATE is specified.
            if (!(flags & 2) &&
                (contents.buffer === buffer || contents.buffer === buffer.buffer)) {
                // We can't emulate MAP_SHARED when the file is not backed by the buffer
                // we're mapping to (e.g. the HEAP buffer).
                allocated = false;
                ptr = contents.byteOffset;
            } else {
                // Try to avoid unnecessary slices.
                if (position > 0 || position + length < contents.length) {
                    if (contents.subarray) {
                        contents = contents.subarray(position, position + length);
                    } else {
                        contents = Array.prototype.slice.call(contents, position, position + length);
                    }
                }
                allocated = true;
                ptr = _malloc(length);
                if (!ptr) {
                    throw new FS.ErrnoError(ERRNO_CODES.ENOMEM);
                }
                buffer.set(contents, ptr);
            }
            return {
                ptr: ptr,
                allocated: allocated
            };
        }
    }
};

var IDBFS = {
    dbs: {},
    indexedDB: function() {
        return window.indexedDB || window.mozIndexedDB || window.webkitIndexedDB || window.msIndexedDB;
    },
    DB_VERSION: 20,
    DB_STORE_NAME: "FILE_DATA",
    mount: function(mount) {
        return MEMFS.mount.apply(null, arguments);
    },
    syncfs: function(mount, populate, callback) {
        IDBFS.getLocalSet(mount, function(err, local) {
            if (err) return callback(err);

            IDBFS.getRemoteSet(mount, function(err, remote) {
                if (err) return callback(err);

                var src = populate ? remote : local;
                var dst = populate ? local : remote;

                IDBFS.reconcile(src, dst, callback);
            });
        });
    },
    reconcile: function(src, dst, callback) {
        var total = 0;

        var create = {};
        for (var key in src.files) {
            if (!src.files.hasOwnProperty(key)) continue;
            var e = src.files[key];
            var e2 = dst.files[key];
            if (!e2 || e.timestamp > e2.timestamp) {
                create[key] = e;
                total++;
            }
        }

        var remove = {};
        for (var key in dst.files) {
            if (!dst.files.hasOwnProperty(key)) continue;
            var e = dst.files[key];
            var e2 = src.files[key];
            if (!e2) {
                remove[key] = e;
                total++;
            }
        }

        if (!total) {
            // early out
            return callback(null);
        }

        var completed = 0;

        function done(err) {
            if (err) return callback(err);
            if (++completed >= total) {
                return callback(null);
            }
        };

        // create a single transaction to handle and IDB reads / writes we'll need to do
        var db = src.type === 'remote' ? src.db : dst.db;
        var transaction = db.transaction([IDBFS.DB_STORE_NAME], 'readwrite');
        transaction.onerror = function transaction_onerror() {
            callback(this.error);
        };
        var store = transaction.objectStore(IDBFS.DB_STORE_NAME);

        for (var path in create) {
            if (!create.hasOwnProperty(path)) continue;
            var entry = create[path];

            if (dst.type === 'local') {
                // save file to local
                try {
                    if (FS.isDir(entry.mode)) {
                        FS.mkdir(path, entry.mode);
                    } else if (FS.isFile(entry.mode)) {
                        var stream = FS.open(path, 'w+', 0666);
                        FS.write(stream, entry.contents, 0, entry.contents.length, 0, true /* canOwn */ );
                        FS.close(stream);
                    }
                    done(null);
                } catch (e) {
                    return done(e);
                }
            } else {
                // save file to IDB
                var req = store.put(entry, path);
                req.onsuccess = function req_onsuccess() {
                    done(null);
                };
                req.onerror = function req_onerror() {
                    done(this.error);
                };
            }
        }

        for (var path in remove) {
            if (!remove.hasOwnProperty(path)) continue;
            var entry = remove[path];

            if (dst.type === 'local') {
                // delete file from local
                try {
                    if (FS.isDir(entry.mode)) {
                        // TODO recursive delete?
                        FS.rmdir(path);
                    } else if (FS.isFile(entry.mode)) {
                        FS.unlink(path);
                    }
                    done(null);
                } catch (e) {
                    return done(e);
                }
            } else {
                // delete file from IDB
                var req = store.delete(path);
                req.onsuccess = function req_onsuccess() {
                    done(null);
                };
                req.onerror = function req_onerror() {
                    done(this.error);
                };
            }
        }
    },
    getLocalSet: function(mount, callback) {
        var files = {};

        function isRealDir(p) {
            return p !== '.' && p !== '..';
        };

        function toAbsolute(root) {
            return function(p) {
                return PATH.join2(root, p);
            }
        };

        var check = FS.readdir(mount.mountpoint)
            .filter(isRealDir)
            .map(toAbsolute(mount.mountpoint));

        while (check.length) {
            var path = check.pop();
            var stat, node;

            try {
                var lookup = FS.lookupPath(path);
                node = lookup.node;
                stat = FS.stat(path);
            } catch (e) {
                return callback(e);
            }

            if (FS.isDir(stat.mode)) {
                check.push.apply(check, FS.readdir(path)
                    .filter(isRealDir)
                    .map(toAbsolute(path)));

                files[path] = {
                    mode: stat.mode,
                    timestamp: stat.mtime
                };
            } else if (FS.isFile(stat.mode)) {
                files[path] = {
                    contents: node.contents,
                    mode: stat.mode,
                    timestamp: stat.mtime
                };
            } else {
                return callback(new Error('node type not supported'));
            }
        }

        return callback(null, {
            type: 'local',
            files: files
        });
    },
    getDB: function(name, callback) {
        // look it up in the cache
        var db = IDBFS.dbs[name];
        if (db) {
            return callback(null, db);
        }
        var req;
        try {
            req = IDBFS.indexedDB().open(name, IDBFS.DB_VERSION);
        } catch (e) {
            return onerror(e);
        }
        req.onupgradeneeded = function req_onupgradeneeded() {
            db = req.result;
            db.createObjectStore(IDBFS.DB_STORE_NAME);
        };
        req.onsuccess = function req_onsuccess() {
            db = req.result;
            // add to the cache
            IDBFS.dbs[name] = db;
            callback(null, db);
        };
        req.onerror = function req_onerror() {
            callback(this.error);
        };
    },
    getRemoteSet: function(mount, callback) {
        var files = {};

        IDBFS.getDB(mount.mountpoint, function(err, db) {
            if (err) return callback(err);

            var transaction = db.transaction([IDBFS.DB_STORE_NAME], 'readonly');
            transaction.onerror = function transaction_onerror() {
                callback(this.error);
            };

            var store = transaction.objectStore(IDBFS.DB_STORE_NAME);
            store.openCursor().onsuccess = function store_openCursor_onsuccess(event) {
                var cursor = event.target.result;
                if (!cursor) {
                    return callback(null, {
                        type: 'remote',
                        db: db,
                        files: files
                    });
                }

                files[cursor.key] = cursor.value;
                cursor.continue();
            };
        });
    }
};

var NODEFS = {
    isWindows: false,
    staticInit: function() {
        NODEFS.isWindows = !!process.platform.match(/^win/);
    },
    mount: function(mount) {
        assert(ENVIRONMENT_IS_NODE);
        return NODEFS.createNode(null, '/', NODEFS.getMode(mount.opts.root), 0);
    },
    createNode: function(parent, name, mode, dev) {
        if (!FS.isDir(mode) && !FS.isFile(mode) && !FS.isLink(mode)) {
            throw new FS.ErrnoError(ERRNO_CODES.EINVAL);
        }
        var node = FS.createNode(parent, name, mode);
        node.node_ops = NODEFS.node_ops;
        node.stream_ops = NODEFS.stream_ops;
        return node;
    },
    getMode: function(path) {
        var stat;
        try {
            stat = fs.lstatSync(path);
            if (NODEFS.isWindows) {
                // On Windows, directories return permission bits 'rw-rw-rw-', even though they have 'rwxrwxrwx', so 
                // propagate write bits to execute bits.
                stat.mode = stat.mode | ((stat.mode & 146) >> 1);
            }
        } catch (e) {
            if (!e.code) throw e;
            throw new FS.ErrnoError(ERRNO_CODES[e.code]);
        }
        return stat.mode;
    },
    realPath: function(node) {
        var parts = [];
        while (node.parent !== node) {
            parts.push(node.name);
            node = node.parent;
        }
        parts.push(node.mount.opts.root);
        parts.reverse();
        return PATH.join.apply(null, parts);
    },
    flagsToPermissionStringMap: {
        0: "r",
        1: "r+",
        2: "r+",
        64: "r",
        65: "r+",
        66: "r+",
        129: "rx+",
        193: "rx+",
        514: "w+",
        577: "w",
        578: "w+",
        705: "wx",
        706: "wx+",
        1024: "a",
        1025: "a",
        1026: "a+",
        1089: "a",
        1090: "a+",
        1153: "ax",
        1154: "ax+",
        1217: "ax",
        1218: "ax+",
        4096: "rs",
        4098: "rs+"
    },
    flagsToPermissionString: function(flags) {
        if (flags in NODEFS.flagsToPermissionStringMap) {
            return NODEFS.flagsToPermissionStringMap[flags];
        } else {
            return flags;
        }
    },
    node_ops: {
        getattr: function(node) {
            var path = NODEFS.realPath(node);
            var stat;
            try {
                stat = fs.lstatSync(path);
            } catch (e) {
                if (!e.code) throw e;
                throw new FS.ErrnoError(ERRNO_CODES[e.code]);
            }
            // node.js v0.10.20 doesn't report blksize and blocks on Windows. Fake them with default blksize of 4096.
            // See http://support.microsoft.com/kb/140365
            if (NODEFS.isWindows && !stat.blksize) {
                stat.blksize = 4096;
            }
            if (NODEFS.isWindows && !stat.blocks) {
                stat.blocks = (stat.size + stat.blksize - 1) / stat.blksize | 0;
            }
            return {
                dev: stat.dev,
                ino: stat.ino,
                mode: stat.mode,
                nlink: stat.nlink,
                uid: stat.uid,
                gid: stat.gid,
                rdev: stat.rdev,
                size: stat.size,
                atime: stat.atime,
                mtime: stat.mtime,
                ctime: stat.ctime,
                blksize: stat.blksize,
                blocks: stat.blocks
            };
        },
        setattr: function(node, attr) {
            var path = NODEFS.realPath(node);
            try {
                if (attr.mode !== undefined) {
                    fs.chmodSync(path, attr.mode);
                    // update the common node structure mode as well
                    node.mode = attr.mode;
                }
                if (attr.timestamp !== undefined) {
                    var date = new Date(attr.timestamp);
                    fs.utimesSync(path, date, date);
                }
                if (attr.size !== undefined) {
                    fs.truncateSync(path, attr.size);
                }
            } catch (e) {
                if (!e.code) throw e;
                throw new FS.ErrnoError(ERRNO_CODES[e.code]);
            }
        },
        lookup: function(parent, name) {
            var path = PATH.join2(NODEFS.realPath(parent), name);
            var mode = NODEFS.getMode(path);
            return NODEFS.createNode(parent, name, mode);
        },
        mknod: function(parent, name, mode, dev) {
            var node = NODEFS.createNode(parent, name, mode, dev);
            // create the backing node for this in the fs root as well
            var path = NODEFS.realPath(node);
            try {
                if (FS.isDir(node.mode)) {
                    fs.mkdirSync(path, node.mode);
                } else {
                    fs.writeFileSync(path, '', {
                        mode: node.mode
                    });
                }
            } catch (e) {
                if (!e.code) throw e;
                throw new FS.ErrnoError(ERRNO_CODES[e.code]);
            }
            return node;
        },
        rename: function(oldNode, newDir, newName) {
            var oldPath = NODEFS.realPath(oldNode);
            var newPath = PATH.join2(NODEFS.realPath(newDir), newName);
            try {
                fs.renameSync(oldPath, newPath);
            } catch (e) {
                if (!e.code) throw e;
                throw new FS.ErrnoError(ERRNO_CODES[e.code]);
            }
        },
        unlink: function(parent, name) {
            var path = PATH.join2(NODEFS.realPath(parent), name);
            try {
                fs.unlinkSync(path);
            } catch (e) {
                if (!e.code) throw e;
                throw new FS.ErrnoError(ERRNO_CODES[e.code]);
            }
        },
        rmdir: function(parent, name) {
            var path = PATH.join2(NODEFS.realPath(parent), name);
            try {
                fs.rmdirSync(path);
            } catch (e) {
                if (!e.code) throw e;
                throw new FS.ErrnoError(ERRNO_CODES[e.code]);
            }
        },
        readdir: function(node) {
            var path = NODEFS.realPath(node);
            try {
                return fs.readdirSync(path);
            } catch (e) {
                if (!e.code) throw e;
                throw new FS.ErrnoError(ERRNO_CODES[e.code]);
            }
        },
        symlink: function(parent, newName, oldPath) {
            var newPath = PATH.join2(NODEFS.realPath(parent), newName);
            try {
                fs.symlinkSync(oldPath, newPath);
            } catch (e) {
                if (!e.code) throw e;
                throw new FS.ErrnoError(ERRNO_CODES[e.code]);
            }
        },
        readlink: function(node) {
            var path = NODEFS.realPath(node);
            try {
                return fs.readlinkSync(path);
            } catch (e) {
                if (!e.code) throw e;
                throw new FS.ErrnoError(ERRNO_CODES[e.code]);
            }
        }
    },
    stream_ops: {
        open: function(stream) {
            var path = NODEFS.realPath(stream.node);
            try {
                if (FS.isFile(stream.node.mode)) {
                    stream.nfd = fs.openSync(path, NODEFS.flagsToPermissionString(stream.flags));
                }
            } catch (e) {
                if (!e.code) throw e;
                throw new FS.ErrnoError(ERRNO_CODES[e.code]);
            }
        },
        close: function(stream) {
            try {
                if (FS.isFile(stream.node.mode) && stream.nfd) {
                    fs.closeSync(stream.nfd);
                }
            } catch (e) {
                if (!e.code) throw e;
                throw new FS.ErrnoError(ERRNO_CODES[e.code]);
            }
        },
        read: function(stream, buffer, offset, length, position) {
            // FIXME this is terrible.
            var nbuffer = new Buffer(length);
            var res;
            try {
                res = fs.readSync(stream.nfd, nbuffer, 0, length, position);
            } catch (e) {
                throw new FS.ErrnoError(ERRNO_CODES[e.code]);
            }
            if (res > 0) {
                for (var i = 0; i < res; i++) {
                    buffer[offset + i] = nbuffer[i];
                }
            }
            return res;
        },
        write: function(stream, buffer, offset, length, position) {
            // FIXME this is terrible.
            var nbuffer = new Buffer(buffer.subarray(offset, offset + length));
            var res;
            try {
                res = fs.writeSync(stream.nfd, nbuffer, 0, length, position);
            } catch (e) {
                throw new FS.ErrnoError(ERRNO_CODES[e.code]);
            }
            return res;
        },
        llseek: function(stream, offset, whence) {
            var position = offset;
            if (whence === 1) { // SEEK_CUR.
                position += stream.position;
            } else if (whence === 2) { // SEEK_END.
                if (FS.isFile(stream.node.mode)) {
                    try {
                        var stat = fs.fstatSync(stream.nfd);
                        position += stat.size;
                    } catch (e) {
                        throw new FS.ErrnoError(ERRNO_CODES[e.code]);
                    }
                }
            }

            if (position < 0) {
                throw new FS.ErrnoError(ERRNO_CODES.EINVAL);
            }

            stream.position = position;
            return position;
        }
    }
};

var _stdin = allocate(1, "i32*", ALLOC_STATIC);

var _stdout = allocate(1, "i32*", ALLOC_STATIC);

var _stderr = allocate(1, "i32*", ALLOC_STATIC);

function _fflush(stream) {
    // int fflush(FILE *stream);
    // http://pubs.opengroup.org/onlinepubs/000095399/functions/fflush.html
    // we don't currently perform any user-space buffering of data
}
var FS = {
    root: null,
    mounts: [],
    devices: [null],
    streams: [null],
    nextInode: 1,
    nameTable: null,
    currentPath: "/",
    initialized: false,
    ignorePermissions: true,
    ErrnoError: null,
    genericErrors: {},
    handleFSError: function(e) {
        if (!(e instanceof FS.ErrnoError)) throw e + ' : ' + stackTrace();
        return ___setErrNo(e.errno);
    },
    lookupPath: function(path, opts) {
        path = PATH.resolve(FS.cwd(), path);
        opts = opts || {
            recurse_count: 0
        };

        if (opts.recurse_count > 8) { // max recursive lookup of 8
            throw new FS.ErrnoError(ERRNO_CODES.ELOOP);
        }

        // split the path
        var parts = PATH.normalizeArray(path.split('/').filter(function(p) {
            return !!p;
        }), false);

        // start at the root
        var current = FS.root;
        var current_path = '/';

        for (var i = 0; i < parts.length; i++) {
            var islast = (i === parts.length - 1);
            if (islast && opts.parent) {
                // stop resolving
                break;
            }

            current = FS.lookupNode(current, parts[i]);
            current_path = PATH.join2(current_path, parts[i]);

            // jump to the mount's root node if this is a mountpoint
            if (FS.isMountpoint(current)) {
                current = current.mount.root;
            }

            // follow symlinks
            // by default, lookupPath will not follow a symlink if it is the final path component.
            // setting opts.follow = true will override this behavior.
            if (!islast || opts.follow) {
                var count = 0;
                while (FS.isLink(current.mode)) {
                    var link = FS.readlink(current_path);
                    current_path = PATH.resolve(PATH.dirname(current_path), link);

                    var lookup = FS.lookupPath(current_path, {
                        recurse_count: opts.recurse_count
                    });
                    current = lookup.node;

                    if (count++ > 40) { // limit max consecutive symlinks to 40 (SYMLOOP_MAX).
                        throw new FS.ErrnoError(ERRNO_CODES.ELOOP);
                    }
                }
            }
        }

        return {
            path: current_path,
            node: current
        };
    },
    getPath: function(node) {
        var path;
        while (true) {
            if (FS.isRoot(node)) {
                var mount = node.mount.mountpoint;
                if (!path) return mount;
                return mount[mount.length - 1] !== '/' ? mount + '/' + path : mount + path;
            }
            path = path ? node.name + '/' + path : node.name;
            node = node.parent;
        }
    },
    hashName: function(parentid, name) {
        var hash = 0;


        for (var i = 0; i < name.length; i++) {
            hash = ((hash << 5) - hash + name.charCodeAt(i)) | 0;
        }
        return ((parentid + hash) >>> 0) % FS.nameTable.length;
    },
    hashAddNode: function(node) {
        var hash = FS.hashName(node.parent.id, node.name);
        node.name_next = FS.nameTable[hash];
        FS.nameTable[hash] = node;
    },
    hashRemoveNode: function(node) {
        var hash = FS.hashName(node.parent.id, node.name);
        if (FS.nameTable[hash] === node) {
            FS.nameTable[hash] = node.name_next;
        } else {
            var current = FS.nameTable[hash];
            while (current) {
                if (current.name_next === node) {
                    current.name_next = node.name_next;
                    break;
                }
                current = current.name_next;
            }
        }
    },
    lookupNode: function(parent, name) {
        var err = FS.mayLookup(parent);
        if (err) {
            throw new FS.ErrnoError(err);
        }
        var hash = FS.hashName(parent.id, name);
        for (var node = FS.nameTable[hash]; node; node = node.name_next) {
            var nodeName = node.name;
            if (node.parent.id === parent.id && nodeName === name) {
                return node;
            }
        }
        // if we failed to find it in the cache, call into the VFS
        return FS.lookup(parent, name);
    },
    createNode: function(parent, name, mode, rdev) {
        if (!FS.FSNode) {
            FS.FSNode = function(parent, name, mode, rdev) {
                this.id = FS.nextInode++;
                this.name = name;
                this.mode = mode;
                this.node_ops = {};
                this.stream_ops = {};
                this.rdev = rdev;
                this.parent = null;
                this.mount = null;
                if (!parent) {
                    parent = this; // root node sets parent to itself
                }
                this.parent = parent;
                this.mount = parent.mount;
                FS.hashAddNode(this);
            };

            // compatibility
            var readMode = 292 | 73;
            var writeMode = 146;

            FS.FSNode.prototype = {};

            // NOTE we must use Object.defineProperties instead of individual calls to
            // Object.defineProperty in order to make closure compiler happy
            Object.defineProperties(FS.FSNode.prototype, {
                read: {
                    get: function() {
                        return (this.mode & readMode) === readMode;
                    },
                    set: function(val) {
                        val ? this.mode |= readMode : this.mode &= ~readMode;
                    }
                },
                write: {
                    get: function() {
                        return (this.mode & writeMode) === writeMode;
                    },
                    set: function(val) {
                        val ? this.mode |= writeMode : this.mode &= ~writeMode;
                    }
                },
                isFolder: {
                    get: function() {
                        return FS.isDir(this.mode);
                    },
                },
                isDevice: {
                    get: function() {
                        return FS.isChrdev(this.mode);
                    },
                },
            });
        }
        return new FS.FSNode(parent, name, mode, rdev);
    },
    destroyNode: function(node) {
        FS.hashRemoveNode(node);
    },
    isRoot: function(node) {
        return node === node.parent;
    },
    isMountpoint: function(node) {
        return node.mounted;
    },
    isFile: function(mode) {
        return (mode & 61440) === 32768;
    },
    isDir: function(mode) {
        return (mode & 61440) === 16384;
    },
    isLink: function(mode) {
        return (mode & 61440) === 40960;
    },
    isChrdev: function(mode) {
        return (mode & 61440) === 8192;
    },
    isBlkdev: function(mode) {
        return (mode & 61440) === 24576;
    },
    isFIFO: function(mode) {
        return (mode & 61440) === 4096;
    },
    isSocket: function(mode) {
        return (mode & 49152) === 49152;
    },
    flagModes: {
        "r": 0,
        "rs": 1052672,
        "r+": 2,
        "w": 577,
        "wx": 705,
        "xw": 705,
        "w+": 578,
        "wx+": 706,
        "xw+": 706,
        "a": 1089,
        "ax": 1217,
        "xa": 1217,
        "a+": 1090,
        "ax+": 1218,
        "xa+": 1218
    },
    modeStringToFlags: function(str) {
        var flags = FS.flagModes[str];
        if (typeof flags === 'undefined') {
            throw new Error('Unknown file open mode: ' + str);
        }
        return flags;
    },
    flagsToPermissionString: function(flag) {
        var accmode = flag & 2097155;
        var perms = ['r', 'w', 'rw'][accmode];
        if ((flag & 512)) {
            perms += 'w';
        }
        return perms;
    },
    nodePermissions: function(node, perms) {
        if (FS.ignorePermissions) {
            return 0;
        }
        // return 0 if any user, group or owner bits are set.
        if (perms.indexOf('r') !== -1 && !(node.mode & 292)) {
            return ERRNO_CODES.EACCES;
        } else if (perms.indexOf('w') !== -1 && !(node.mode & 146)) {
            return ERRNO_CODES.EACCES;
        } else if (perms.indexOf('x') !== -1 && !(node.mode & 73)) {
            return ERRNO_CODES.EACCES;
        }
        return 0;
    },
    mayLookup: function(dir) {
        return FS.nodePermissions(dir, 'x');
    },
    mayCreate: function(dir, name) {
        try {
            var node = FS.lookupNode(dir, name);
            return ERRNO_CODES.EEXIST;
        } catch (e) {}
        return FS.nodePermissions(dir, 'wx');
    },
    mayDelete: function(dir, name, isdir) {
        var node;
        try {
            node = FS.lookupNode(dir, name);
        } catch (e) {
            return e.errno;
        }
        var err = FS.nodePermissions(dir, 'wx');
        if (err) {
            return err;
        }
        if (isdir) {
            if (!FS.isDir(node.mode)) {
                return ERRNO_CODES.ENOTDIR;
            }
            if (FS.isRoot(node) || FS.getPath(node) === FS.cwd()) {
                return ERRNO_CODES.EBUSY;
            }
        } else {
            if (FS.isDir(node.mode)) {
                return ERRNO_CODES.EISDIR;
            }
        }
        return 0;
    },
    mayOpen: function(node, flags) {
        if (!node) {
            return ERRNO_CODES.ENOENT;
        }
        if (FS.isLink(node.mode)) {
            return ERRNO_CODES.ELOOP;
        } else if (FS.isDir(node.mode)) {
            if ((flags & 2097155) !== 0 || // opening for write
                (flags & 512)) {
                return ERRNO_CODES.EISDIR;
            }
        }
        return FS.nodePermissions(node, FS.flagsToPermissionString(flags));
    },
    MAX_OPEN_FDS: 4096,
    nextfd: function(fd_start, fd_end) {
        fd_start = fd_start || 1;
        fd_end = fd_end || FS.MAX_OPEN_FDS;
        for (var fd = fd_start; fd <= fd_end; fd++) {
            if (!FS.streams[fd]) {
                return fd;
            }
        }
        throw new FS.ErrnoError(ERRNO_CODES.EMFILE);
    },
    getStream: function(fd) {
        return FS.streams[fd];
    },
    createStream: function(stream, fd_start, fd_end) {
        if (!FS.FSStream) {
            FS.FSStream = function() {};
            FS.FSStream.prototype = {};
            // compatibility
            Object.defineProperties(FS.FSStream.prototype, {
                object: {
                    get: function() {
                        return this.node;
                    },
                    set: function(val) {
                        this.node = val;
                    }
                },
                isRead: {
                    get: function() {
                        return (this.flags & 2097155) !== 1;
                    }
                },
                isWrite: {
                    get: function() {
                        return (this.flags & 2097155) !== 0;
                    }
                },
                isAppend: {
                    get: function() {
                        return (this.flags & 1024);
                    }
                }
            });
        }
        if (stream.__proto__) {
            // reuse the object
            stream.__proto__ = FS.FSStream.prototype;
        } else {
            var newStream = new FS.FSStream();
            for (var p in stream) {
                newStream[p] = stream[p];
            }
            stream = newStream;
        }
        var fd = FS.nextfd(fd_start, fd_end);
        stream.fd = fd;
        FS.streams[fd] = stream;
        return stream;
    },
    closeStream: function(fd) {
        FS.streams[fd] = null;
    },
    chrdev_stream_ops: {
        open: function(stream) {
            var device = FS.getDevice(stream.node.rdev);
            // override node's stream ops with the device's
            stream.stream_ops = device.stream_ops;
            // forward the open call
            if (stream.stream_ops.open) {
                stream.stream_ops.open(stream);
            }
        },
        llseek: function() {
            throw new FS.ErrnoError(ERRNO_CODES.ESPIPE);
        }
    },
    major: function(dev) {
        return ((dev) >> 8);
    },
    minor: function(dev) {
        return ((dev) & 0xff);
    },
    makedev: function(ma, mi) {
        return ((ma) << 8 | (mi));
    },
    registerDevice: function(dev, ops) {
        FS.devices[dev] = {
            stream_ops: ops
        };
    },
    getDevice: function(dev) {
        return FS.devices[dev];
    },
    syncfs: function(populate, callback) {
        if (typeof(populate) === 'function') {
            callback = populate;
            populate = false;
        }

        var completed = 0;
        var total = FS.mounts.length;

        function done(err) {
            if (err) {
                return callback(err);
            }
            if (++completed >= total) {
                callback(null);
            }
        };

        // sync all mounts
        for (var i = 0; i < FS.mounts.length; i++) {
            var mount = FS.mounts[i];
            if (!mount.type.syncfs) {
                done(null);
                continue;
            }
            mount.type.syncfs(mount, populate, done);
        }
    },
    mount: function(type, opts, mountpoint) {
        var lookup;
        if (mountpoint) {
            lookup = FS.lookupPath(mountpoint, {
                follow: false
            });
            mountpoint = lookup.path; // use the absolute path
        }
        var mount = {
            type: type,
            opts: opts,
            mountpoint: mountpoint,
            root: null
        };
        // create a root node for the fs
        var root = type.mount(mount);
        root.mount = mount;
        mount.root = root;
        // assign the mount info to the mountpoint's node
        if (lookup) {
            lookup.node.mount = mount;
            lookup.node.mounted = true;
            // compatibility update FS.root if we mount to /
            if (mountpoint === '/') {
                FS.root = mount.root;
            }
        }
        // add to our cached list of mounts
        FS.mounts.push(mount);
        return root;
    },
    lookup: function(parent, name) {
        return parent.node_ops.lookup(parent, name);
    },
    mknod: function(path, mode, dev) {
        var lookup = FS.lookupPath(path, {
            parent: true
        });
        var parent = lookup.node;
        var name = PATH.basename(path);
        var err = FS.mayCreate(parent, name);
        if (err) {
            throw new FS.ErrnoError(err);
        }
        if (!parent.node_ops.mknod) {
            throw new FS.ErrnoError(ERRNO_CODES.EPERM);
        }
        return parent.node_ops.mknod(parent, name, mode, dev);
    },
    create: function(path, mode) {
        mode = mode !== undefined ? mode : 0666;
        mode &= 4095;
        mode |= 32768;
        return FS.mknod(path, mode, 0);
    },
    mkdir: function(path, mode) {
        mode = mode !== undefined ? mode : 0777;
        mode &= 511 | 512;
        mode |= 16384;
        return FS.mknod(path, mode, 0);
    },
    mkdev: function(path, mode, dev) {
        if (typeof(dev) === 'undefined') {
            dev = mode;
            mode = 0666;
        }
        mode |= 8192;
        return FS.mknod(path, mode, dev);
    },
    symlink: function(oldpath, newpath) {
        var lookup = FS.lookupPath(newpath, {
            parent: true
        });
        var parent = lookup.node;
        var newname = PATH.basename(newpath);
        var err = FS.mayCreate(parent, newname);
        if (err) {
            throw new FS.ErrnoError(err);
        }
        if (!parent.node_ops.symlink) {
            throw new FS.ErrnoError(ERRNO_CODES.EPERM);
        }
        return parent.node_ops.symlink(parent, newname, oldpath);
    },
    rename: function(old_path, new_path) {
        var old_dirname = PATH.dirname(old_path);
        var new_dirname = PATH.dirname(new_path);
        var old_name = PATH.basename(old_path);
        var new_name = PATH.basename(new_path);
        // parents must exist
        var lookup, old_dir, new_dir;
        try {
            lookup = FS.lookupPath(old_path, {
                parent: true
            });
            old_dir = lookup.node;
            lookup = FS.lookupPath(new_path, {
                parent: true
            });
            new_dir = lookup.node;
        } catch (e) {
            throw new FS.ErrnoError(ERRNO_CODES.EBUSY);
        }
        // need to be part of the same mount
        if (old_dir.mount !== new_dir.mount) {
            throw new FS.ErrnoError(ERRNO_CODES.EXDEV);
        }
        // source must exist
        var old_node = FS.lookupNode(old_dir, old_name);
        // old path should not be an ancestor of the new path
        var relative = PATH.relative(old_path, new_dirname);
        if (relative.charAt(0) !== '.') {
            throw new FS.ErrnoError(ERRNO_CODES.EINVAL);
        }
        // new path should not be an ancestor of the old path
        relative = PATH.relative(new_path, old_dirname);
        if (relative.charAt(0) !== '.') {
            throw new FS.ErrnoError(ERRNO_CODES.ENOTEMPTY);
        }
        // see if the new path already exists
        var new_node;
        try {
            new_node = FS.lookupNode(new_dir, new_name);
        } catch (e) {
            // not fatal
        }
        // early out if nothing needs to change
        if (old_node === new_node) {
            return;
        }
        // we'll need to delete the old entry
        var isdir = FS.isDir(old_node.mode);
        var err = FS.mayDelete(old_dir, old_name, isdir);
        if (err) {
            throw new FS.ErrnoError(err);
        }
        // need delete permissions if we'll be overwriting.
        // need create permissions if new doesn't already exist.
        err = new_node ?
            FS.mayDelete(new_dir, new_name, isdir) :
            FS.mayCreate(new_dir, new_name);
        if (err) {
            throw new FS.ErrnoError(err);
        }
        if (!old_dir.node_ops.rename) {
            throw new FS.ErrnoError(ERRNO_CODES.EPERM);
        }
        if (FS.isMountpoint(old_node) || (new_node && FS.isMountpoint(new_node))) {
            throw new FS.ErrnoError(ERRNO_CODES.EBUSY);
        }
        // if we are going to change the parent, check write permissions
        if (new_dir !== old_dir) {
            err = FS.nodePermissions(old_dir, 'w');
            if (err) {
                throw new FS.ErrnoError(err);
            }
        }
        // remove the node from the lookup hash
        FS.hashRemoveNode(old_node);
        // do the underlying fs rename
        try {
            old_dir.node_ops.rename(old_node, new_dir, new_name);
        } catch (e) {
            throw e;
        } finally {
            // add the node back to the hash (in case node_ops.rename
            // changed its name)
            FS.hashAddNode(old_node);
        }
    },
    rmdir: function(path) {
        var lookup = FS.lookupPath(path, {
            parent: true
        });
        var parent = lookup.node;
        var name = PATH.basename(path);
        var node = FS.lookupNode(parent, name);
        var err = FS.mayDelete(parent, name, true);
        if (err) {
            throw new FS.ErrnoError(err);
        }
        if (!parent.node_ops.rmdir) {
            throw new FS.ErrnoError(ERRNO_CODES.EPERM);
        }
        if (FS.isMountpoint(node)) {
            throw new FS.ErrnoError(ERRNO_CODES.EBUSY);
        }
        parent.node_ops.rmdir(parent, name);
        FS.destroyNode(node);
    },
    readdir: function(path) {
        var lookup = FS.lookupPath(path, {
            follow: true
        });
        var node = lookup.node;
        if (!node.node_ops.readdir) {
            throw new FS.ErrnoError(ERRNO_CODES.ENOTDIR);
        }
        return node.node_ops.readdir(node);
    },
    unlink: function(path) {
        var lookup = FS.lookupPath(path, {
            parent: true
        });
        var parent = lookup.node;
        var name = PATH.basename(path);
        var node = FS.lookupNode(parent, name);
        var err = FS.mayDelete(parent, name, false);
        if (err) {
            // POSIX says unlink should set EPERM, not EISDIR
            if (err === ERRNO_CODES.EISDIR) err = ERRNO_CODES.EPERM;
            throw new FS.ErrnoError(err);
        }
        if (!parent.node_ops.unlink) {
            throw new FS.ErrnoError(ERRNO_CODES.EPERM);
        }
        if (FS.isMountpoint(node)) {
            throw new FS.ErrnoError(ERRNO_CODES.EBUSY);
        }
        parent.node_ops.unlink(parent, name);
        FS.destroyNode(node);
    },
    readlink: function(path) {
        var lookup = FS.lookupPath(path, {
            follow: false
        });
        var link = lookup.node;
        if (!link.node_ops.readlink) {
            throw new FS.ErrnoError(ERRNO_CODES.EINVAL);
        }
        return link.node_ops.readlink(link);
    },
    stat: function(path, dontFollow) {
        var lookup = FS.lookupPath(path, {
            follow: !dontFollow
        });
        var node = lookup.node;
        if (!node.node_ops.getattr) {
            throw new FS.ErrnoError(ERRNO_CODES.EPERM);
        }
        return node.node_ops.getattr(node);
    },
    lstat: function(path) {
        return FS.stat(path, true);
    },
    chmod: function(path, mode, dontFollow) {
        var node;
        if (typeof path === 'string') {
            var lookup = FS.lookupPath(path, {
                follow: !dontFollow
            });
            node = lookup.node;
        } else {
            node = path;
        }
        if (!node.node_ops.setattr) {
            throw new FS.ErrnoError(ERRNO_CODES.EPERM);
        }
        node.node_ops.setattr(node, {
            mode: (mode & 4095) | (node.mode & ~4095),
            timestamp: Date.now()
        });
    },
    lchmod: function(path, mode) {
        FS.chmod(path, mode, true);
    },
    fchmod: function(fd, mode) {
        var stream = FS.getStream(fd);
        if (!stream) {
            throw new FS.ErrnoError(ERRNO_CODES.EBADF);
        }
        FS.chmod(stream.node, mode);
    },
    chown: function(path, uid, gid, dontFollow) {
        var node;
        if (typeof path === 'string') {
            var lookup = FS.lookupPath(path, {
                follow: !dontFollow
            });
            node = lookup.node;
        } else {
            node = path;
        }
        if (!node.node_ops.setattr) {
            throw new FS.ErrnoError(ERRNO_CODES.EPERM);
        }
        node.node_ops.setattr(node, {
            timestamp: Date.now()
                // we ignore the uid / gid for now
        });
    },
    lchown: function(path, uid, gid) {
        FS.chown(path, uid, gid, true);
    },
    fchown: function(fd, uid, gid) {
        var stream = FS.getStream(fd);
        if (!stream) {
            throw new FS.ErrnoError(ERRNO_CODES.EBADF);
        }
        FS.chown(stream.node, uid, gid);
    },
    truncate: function(path, len) {
        if (len < 0) {
            throw new FS.ErrnoError(ERRNO_CODES.EINVAL);
        }
        var node;
        if (typeof path === 'string') {
            var lookup = FS.lookupPath(path, {
                follow: true
            });
            node = lookup.node;
        } else {
            node = path;
        }
        if (!node.node_ops.setattr) {
            throw new FS.ErrnoError(ERRNO_CODES.EPERM);
        }
        if (FS.isDir(node.mode)) {
            throw new FS.ErrnoError(ERRNO_CODES.EISDIR);
        }
        if (!FS.isFile(node.mode)) {
            throw new FS.ErrnoError(ERRNO_CODES.EINVAL);
        }
        var err = FS.nodePermissions(node, 'w');
        if (err) {
            throw new FS.ErrnoError(err);
        }
        node.node_ops.setattr(node, {
            size: len,
            timestamp: Date.now()
        });
    },
    ftruncate: function(fd, len) {
        var stream = FS.getStream(fd);
        if (!stream) {
            throw new FS.ErrnoError(ERRNO_CODES.EBADF);
        }
        if ((stream.flags & 2097155) === 0) {
            throw new FS.ErrnoError(ERRNO_CODES.EINVAL);
        }
        FS.truncate(stream.node, len);
    },
    utime: function(path, atime, mtime) {
        var lookup = FS.lookupPath(path, {
            follow: true
        });
        var node = lookup.node;
        node.node_ops.setattr(node, {
            timestamp: Math.max(atime, mtime)
        });
    },
    open: function(path, flags, mode, fd_start, fd_end) {
        flags = typeof flags === 'string' ? FS.modeStringToFlags(flags) : flags;
        mode = typeof mode === 'undefined' ? 0666 : mode;
        if ((flags & 64)) {
            mode = (mode & 4095) | 32768;
        } else {
            mode = 0;
        }
        var node;
        if (typeof path === 'object') {
            node = path;
        } else {
            path = PATH.normalize(path);
            try {
                var lookup = FS.lookupPath(path, {
                    follow: !(flags & 131072)
                });
                node = lookup.node;
            } catch (e) {
                // ignore
            }
        }
        // perhaps we need to create the node
        if ((flags & 64)) {
            if (node) {
                // if O_CREAT and O_EXCL are set, error out if the node already exists
                if ((flags & 128)) {
                    throw new FS.ErrnoError(ERRNO_CODES.EEXIST);
                }
            } else {
                // node doesn't exist, try to create it
                node = FS.mknod(path, mode, 0);
            }
        }
        if (!node) {
            throw new FS.ErrnoError(ERRNO_CODES.ENOENT);
        }
        // can't truncate a device
        if (FS.isChrdev(node.mode)) {
            flags &= ~512;
        }
        // check permissions
        var err = FS.mayOpen(node, flags);
        if (err) {
            throw new FS.ErrnoError(err);
        }
        // do truncation if necessary
        if ((flags & 512)) {
            FS.truncate(node, 0);
        }
        // we've already handled these, don't pass down to the underlying vfs
        flags &= ~(128 | 512);

        // register the stream with the filesystem
        var stream = FS.createStream({
            node: node,
            path: FS.getPath(node), // we want the absolute path to the node
            flags: flags,
            seekable: true,
            position: 0,
            stream_ops: node.stream_ops,
            // used by the file family libc calls (fopen, fwrite, ferror, etc.)
            ungotten: [],
            error: false
        }, fd_start, fd_end);
        // call the new stream's open function
        if (stream.stream_ops.open) {
            stream.stream_ops.open(stream);
        }
        if (Module['logReadFiles'] && !(flags & 1)) {
            if (!FS.readFiles) FS.readFiles = {};
            if (!(path in FS.readFiles)) {
                FS.readFiles[path] = 1;
                Module['printErr']('read file: ' + path);
            }
        }
        return stream;
    },
    close: function(stream) {
        try {
            if (stream.stream_ops.close) {
                stream.stream_ops.close(stream);
            }
        } catch (e) {
            throw e;
        } finally {
            FS.closeStream(stream.fd);
        }
    },
    llseek: function(stream, offset, whence) {
        if (!stream.seekable || !stream.stream_ops.llseek) {
            throw new FS.ErrnoError(ERRNO_CODES.ESPIPE);
        }
        return stream.stream_ops.llseek(stream, offset, whence);
    },
    read: function(stream, buffer, offset, length, position) {
        if (length < 0 || position < 0) {
            throw new FS.ErrnoError(ERRNO_CODES.EINVAL);
        }
        if ((stream.flags & 2097155) === 1) {
            throw new FS.ErrnoError(ERRNO_CODES.EBADF);
        }
        if (FS.isDir(stream.node.mode)) {
            throw new FS.ErrnoError(ERRNO_CODES.EISDIR);
        }
        if (!stream.stream_ops.read) {
            throw new FS.ErrnoError(ERRNO_CODES.EINVAL);
        }
        var seeking = true;
        if (typeof position === 'undefined') {
            position = stream.position;
            seeking = false;
        } else if (!stream.seekable) {
            throw new FS.ErrnoError(ERRNO_CODES.ESPIPE);
        }
        var bytesRead = stream.stream_ops.read(stream, buffer, offset, length, position);
        if (!seeking) stream.position += bytesRead;
        return bytesRead;
    },
    write: function(stream, buffer, offset, length, position, canOwn) {
        if (length < 0 || position < 0) {
            throw new FS.ErrnoError(ERRNO_CODES.EINVAL);
        }
        if ((stream.flags & 2097155) === 0) {
            throw new FS.ErrnoError(ERRNO_CODES.EBADF);
        }
        if (FS.isDir(stream.node.mode)) {
            throw new FS.ErrnoError(ERRNO_CODES.EISDIR);
        }
        if (!stream.stream_ops.write) {
            throw new FS.ErrnoError(ERRNO_CODES.EINVAL);
        }
        var seeking = true;
        if (typeof position === 'undefined') {
            position = stream.position;
            seeking = false;
        } else if (!stream.seekable) {
            throw new FS.ErrnoError(ERRNO_CODES.ESPIPE);
        }
        if (stream.flags & 1024) {
            // seek to the end before writing in append mode
            FS.llseek(stream, 0, 2);
        }
        var bytesWritten = stream.stream_ops.write(stream, buffer, offset, length, position, canOwn);
        if (!seeking) stream.position += bytesWritten;
        return bytesWritten;
    },
    allocate: function(stream, offset, length) {
        if (offset < 0 || length <= 0) {
            throw new FS.ErrnoError(ERRNO_CODES.EINVAL);
        }
        if ((stream.flags & 2097155) === 0) {
            throw new FS.ErrnoError(ERRNO_CODES.EBADF);
        }
        if (!FS.isFile(stream.node.mode) && !FS.isDir(node.mode)) {
            throw new FS.ErrnoError(ERRNO_CODES.ENODEV);
        }
        if (!stream.stream_ops.allocate) {
            throw new FS.ErrnoError(ERRNO_CODES.EOPNOTSUPP);
        }
        stream.stream_ops.allocate(stream, offset, length);
    },
    mmap: function(stream, buffer, offset, length, position, prot, flags) {
        // TODO if PROT is PROT_WRITE, make sure we have write access
        if ((stream.flags & 2097155) === 1) {
            throw new FS.ErrnoError(ERRNO_CODES.EACCES);
        }
        if (!stream.stream_ops.mmap) {
            throw new FS.ErrnoError(ERRNO_CODES.ENODEV);
        }
        return stream.stream_ops.mmap(stream, buffer, offset, length, position, prot, flags);
    },
    ioctl: function(stream, cmd, arg) {
        if (!stream.stream_ops.ioctl) {
            throw new FS.ErrnoError(ERRNO_CODES.ENOTTY);
        }
        return stream.stream_ops.ioctl(stream, cmd, arg);
    },
    readFile: function(path, opts) {
        opts = opts || {};
        opts.flags = opts.flags || 'r';
        opts.encoding = opts.encoding || 'binary';
        var ret;
        var stream = FS.open(path, opts.flags);
        var stat = FS.stat(path);
        var length = stat.size;
        var buf = new Uint8Array(length);
        FS.read(stream, buf, 0, length, 0);
        if (opts.encoding === 'utf8') {
            ret = '';
            var utf8 = new Runtime.UTF8Processor();
            for (var i = 0; i < length; i++) {
                ret += utf8.processCChar(buf[i]);
            }
        } else if (opts.encoding === 'binary') {
            ret = buf;
        } else {
            throw new Error('Invalid encoding type "' + opts.encoding + '"');
        }
        FS.close(stream);
        return ret;
    },
    writeFile: function(path, data, opts) {
        opts = opts || {};
        opts.flags = opts.flags || 'w';
        opts.encoding = opts.encoding || 'utf8';
        var stream = FS.open(path, opts.flags, opts.mode);
        if (opts.encoding === 'utf8') {
            var utf8 = new Runtime.UTF8Processor();
            var buf = new Uint8Array(utf8.processJSString(data));
            FS.write(stream, buf, 0, buf.length, 0);
        } else if (opts.encoding === 'binary') {
            FS.write(stream, data, 0, data.length, 0);
        } else {
            throw new Error('Invalid encoding type "' + opts.encoding + '"');
        }
        FS.close(stream);
    },
    cwd: function() {
        return FS.currentPath;
    },
    chdir: function(path) {
        var lookup = FS.lookupPath(path, {
            follow: true
        });
        if (!FS.isDir(lookup.node.mode)) {
            throw new FS.ErrnoError(ERRNO_CODES.ENOTDIR);
        }
        var err = FS.nodePermissions(lookup.node, 'x');
        if (err) {
            throw new FS.ErrnoError(err);
        }
        FS.currentPath = lookup.path;
    },
    createDefaultDirectories: function() {
        FS.mkdir('/tmp');
    },
    createDefaultDevices: function() {
        // create /dev
        FS.mkdir('/dev');
        // setup /dev/null
        FS.registerDevice(FS.makedev(1, 3), {
            read: function() {
                return 0;
            },
            write: function() {
                return 0;
            }
        });
        FS.mkdev('/dev/null', FS.makedev(1, 3));
        // setup /dev/tty and /dev/tty1
        // stderr needs to print output using Module['printErr']
        // so we register a second tty just for it.
        TTY.register(FS.makedev(5, 0), TTY.default_tty_ops);
        TTY.register(FS.makedev(6, 0), TTY.default_tty1_ops);
        FS.mkdev('/dev/tty', FS.makedev(5, 0));
        FS.mkdev('/dev/tty1', FS.makedev(6, 0));
        // we're not going to emulate the actual shm device,
        // just create the tmp dirs that reside in it commonly
        FS.mkdir('/dev/shm');
        FS.mkdir('/dev/shm/tmp');
    },
    createStandardStreams: function() {
        // TODO deprecate the old functionality of a single
        // input / output callback and that utilizes FS.createDevice
        // and instead require a unique set of stream ops

        // by default, we symlink the standard streams to the
        // default tty devices. however, if the standard streams
        // have been overwritten we create a unique device for
        // them instead.
        if (Module['stdin']) {
            FS.createDevice('/dev', 'stdin', Module['stdin']);
        } else {
            FS.symlink('/dev/tty', '/dev/stdin');
        }
        if (Module['stdout']) {
            FS.createDevice('/dev', 'stdout', null, Module['stdout']);
        } else {
            FS.symlink('/dev/tty', '/dev/stdout');
        }
        if (Module['stderr']) {
            FS.createDevice('/dev', 'stderr', null, Module['stderr']);
        } else {
            FS.symlink('/dev/tty1', '/dev/stderr');
        }

        // open default streams for the stdin, stdout and stderr devices
        var stdin = FS.open('/dev/stdin', 'r');
        HEAP32[((_stdin) >> 2)] = stdin.fd;
        assert(stdin.fd === 1, 'invalid handle for stdin (' + stdin.fd + ')');

        var stdout = FS.open('/dev/stdout', 'w');
        HEAP32[((_stdout) >> 2)] = stdout.fd;
        assert(stdout.fd === 2, 'invalid handle for stdout (' + stdout.fd + ')');

        var stderr = FS.open('/dev/stderr', 'w');
        HEAP32[((_stderr) >> 2)] = stderr.fd;
        assert(stderr.fd === 3, 'invalid handle for stderr (' + stderr.fd + ')');
    },
    ensureErrnoError: function() {
        if (FS.ErrnoError) return;
        FS.ErrnoError = function ErrnoError(errno) {
            this.errno = errno;
            for (var key in ERRNO_CODES) {
                if (ERRNO_CODES[key] === errno) {
                    this.code = key;
                    break;
                }
            }
            this.message = ERRNO_MESSAGES[errno];
        };
        FS.ErrnoError.prototype = new Error();
        FS.ErrnoError.prototype.constructor = FS.ErrnoError;
        // Some errors may happen quite a bit, to avoid overhead we reuse them (and suffer a lack of stack info)
        [ERRNO_CODES.ENOENT].forEach(function(code) {
            FS.genericErrors[code] = new FS.ErrnoError(code);
            FS.genericErrors[code].stack = '<generic error, no stack>';
        });
    },
    staticInit: function() {
        FS.ensureErrnoError();

        FS.nameTable = new Array(4096);

        FS.root = FS.createNode(null, '/', 16384 | 0777, 0);
        FS.mount(MEMFS, {}, '/');

        FS.createDefaultDirectories();
        FS.createDefaultDevices();
    },
    init: function(input, output, error) {
        assert(!FS.init.initialized, 'FS.init was previously called. If you want to initialize later with custom parameters, remove any earlier calls (note that one is automatically added to the generated code)');
        FS.init.initialized = true;

        FS.ensureErrnoError();

        // Allow Module.stdin etc. to provide defaults, if none explicitly passed to us here
        Module['stdin'] = input || Module['stdin'];
        Module['stdout'] = output || Module['stdout'];
        Module['stderr'] = error || Module['stderr'];

        FS.createStandardStreams();
    },
    quit: function() {
        FS.init.initialized = false;
        for (var i = 0; i < FS.streams.length; i++) {
            var stream = FS.streams[i];
            if (!stream) {
                continue;
            }
            FS.close(stream);
        }
    },
    getMode: function(canRead, canWrite) {
        var mode = 0;
        if (canRead) mode |= 292 | 73;
        if (canWrite) mode |= 146;
        return mode;
    },
    joinPath: function(parts, forceRelative) {
        var path = PATH.join.apply(null, parts);
        if (forceRelative && path[0] == '/') path = path.substr(1);
        return path;
    },
    absolutePath: function(relative, base) {
        return PATH.resolve(base, relative);
    },
    standardizePath: function(path) {
        return PATH.normalize(path);
    },
    findObject: function(path, dontResolveLastLink) {
        var ret = FS.analyzePath(path, dontResolveLastLink);
        if (ret.exists) {
            return ret.object;
        } else {
            ___setErrNo(ret.error);
            return null;
        }
    },
    analyzePath: function(path, dontResolveLastLink) {
        // operate from within the context of the symlink's target
        try {
            var lookup = FS.lookupPath(path, {
                follow: !dontResolveLastLink
            });
            path = lookup.path;
        } catch (e) {}
        var ret = {
            isRoot: false,
            exists: false,
            error: 0,
            name: null,
            path: null,
            object: null,
            parentExists: false,
            parentPath: null,
            parentObject: null
        };
        try {
            var lookup = FS.lookupPath(path, {
                parent: true
            });
            ret.parentExists = true;
            ret.parentPath = lookup.path;
            ret.parentObject = lookup.node;
            ret.name = PATH.basename(path);
            lookup = FS.lookupPath(path, {
                follow: !dontResolveLastLink
            });
            ret.exists = true;
            ret.path = lookup.path;
            ret.object = lookup.node;
            ret.name = lookup.node.name;
            ret.isRoot = lookup.path === '/';
        } catch (e) {
            ret.error = e.errno;
        };
        return ret;
    },
    createFolder: function(parent, name, canRead, canWrite) {
        var path = PATH.join2(typeof parent === 'string' ? parent : FS.getPath(parent), name);
        var mode = FS.getMode(canRead, canWrite);
        return FS.mkdir(path, mode);
    },
    createPath: function(parent, path, canRead, canWrite) {
        parent = typeof parent === 'string' ? parent : FS.getPath(parent);
        var parts = path.split('/').reverse();
        while (parts.length) {
            var part = parts.pop();
            if (!part) continue;
            var current = PATH.join2(parent, part);
            try {
                FS.mkdir(current);
            } catch (e) {
                // ignore EEXIST
            }
            parent = current;
        }
        return current;
    },
    createFile: function(parent, name, properties, canRead, canWrite) {
        var path = PATH.join2(typeof parent === 'string' ? parent : FS.getPath(parent), name);
        var mode = FS.getMode(canRead, canWrite);
        return FS.create(path, mode);
    },
    createDataFile: function(parent, name, data, canRead, canWrite, canOwn) {
        var path = name ? PATH.join2(typeof parent === 'string' ? parent : FS.getPath(parent), name) : parent;
        var mode = FS.getMode(canRead, canWrite);
        var node = FS.create(path, mode);
        if (data) {
            if (typeof data === 'string') {
                var arr = new Array(data.length);
                for (var i = 0, len = data.length; i < len; ++i) arr[i] = data.charCodeAt(i);
                data = arr;
            }
            // make sure we can write to the file
            FS.chmod(node, mode | 146);
            var stream = FS.open(node, 'w');
            FS.write(stream, data, 0, data.length, 0, canOwn);
            FS.close(stream);
            FS.chmod(node, mode);
        }
        return node;
    },
    createDevice: function(parent, name, input, output) {
        var path = PATH.join2(typeof parent === 'string' ? parent : FS.getPath(parent), name);
        var mode = FS.getMode(!!input, !!output);
        if (!FS.createDevice.major) FS.createDevice.major = 64;
        var dev = FS.makedev(FS.createDevice.major++, 0);
        // Create a fake device that a set of stream ops to emulate
        // the old behavior.
        FS.registerDevice(dev, {
            open: function(stream) {
                stream.seekable = false;
            },
            close: function(stream) {
                // flush any pending line data
                if (output && output.buffer && output.buffer.length) {
                    output(10);
                }
            },
            read: function(stream, buffer, offset, length, pos /* ignored */ ) {
                var bytesRead = 0;
                for (var i = 0; i < length; i++) {
                    var result;
                    try {
                        result = input();
                    } catch (e) {
                        throw new FS.ErrnoError(ERRNO_CODES.EIO);
                    }
                    if (result === undefined && bytesRead === 0) {
                        throw new FS.ErrnoError(ERRNO_CODES.EAGAIN);
                    }
                    if (result === null || result === undefined) break;
                    bytesRead++;
                    buffer[offset + i] = result;
                }
                if (bytesRead) {
                    stream.node.timestamp = Date.now();
                }
                return bytesRead;
            },
            write: function(stream, buffer, offset, length, pos) {
                for (var i = 0; i < length; i++) {
                    try {
                        output(buffer[offset + i]);
                    } catch (e) {
                        throw new FS.ErrnoError(ERRNO_CODES.EIO);
                    }
                }
                if (length) {
                    stream.node.timestamp = Date.now();
                }
                return i;
            }
        });
        return FS.mkdev(path, mode, dev);
    },
    createLink: function(parent, name, target, canRead, canWrite) {
        var path = PATH.join2(typeof parent === 'string' ? parent : FS.getPath(parent), name);
        return FS.symlink(target, path);
    },
    forceLoadFile: function(obj) {
        if (obj.isDevice || obj.isFolder || obj.link || obj.contents) return true;
        var success = true;
        if (typeof XMLHttpRequest !== 'undefined') {
            throw new Error("Lazy loading should have been performed (contents set) in createLazyFile, but it was not. Lazy loading only works in web workers. Use --embed-file or --preload-file in emcc on the main thread.");
        } else if (Module['read']) {
            // Command-line.
            try {
                // WARNING: Can't read binary files in V8's d8 or tracemonkey's js, as
                //          read() will try to parse UTF8.
                obj.contents = intArrayFromString(Module['read'](obj.url), true);
            } catch (e) {
                success = false;
            }
        } else {
            throw new Error('Cannot load without read() or XMLHttpRequest.');
        }
        if (!success) ___setErrNo(ERRNO_CODES.EIO);
        return success;
    },
    createLazyFile: function(parent, name, url, canRead, canWrite) {
        if (typeof XMLHttpRequest !== 'undefined') {
            if (!ENVIRONMENT_IS_WORKER) throw 'Cannot do synchronous binary XHRs outside webworkers in modern browsers. Use --embed-file or --preload-file in emcc';
            // Lazy chunked Uint8Array (implements get and length from Uint8Array). Actual getting is abstracted away for eventual reuse.
            function LazyUint8Array() {
                this.lengthKnown = false;
                this.chunks = []; // Loaded chunks. Index is the chunk number
            }
            LazyUint8Array.prototype.get = function LazyUint8Array_get(idx) {
                if (idx > this.length - 1 || idx < 0) {
                    return undefined;
                }
                var chunkOffset = idx % this.chunkSize;
                var chunkNum = Math.floor(idx / this.chunkSize);
                return this.getter(chunkNum)[chunkOffset];
            }
            LazyUint8Array.prototype.setDataGetter = function LazyUint8Array_setDataGetter(getter) {
                this.getter = getter;
            }
            LazyUint8Array.prototype.cacheLength = function LazyUint8Array_cacheLength() {
                // Find length
                var xhr = new XMLHttpRequest();
                xhr.open('HEAD', url, false);
                xhr.send(null);
                if (!(xhr.status >= 200 && xhr.status < 300 || xhr.status === 304)) throw new Error("Couldn't load " + url + ". Status: " + xhr.status);
                var datalength = Number(xhr.getResponseHeader("Content-length"));
                var header;
                var hasByteServing = (header = xhr.getResponseHeader("Accept-Ranges")) && header === "bytes";
                var chunkSize = 1024 * 1024; // Chunk size in bytes

                if (!hasByteServing) chunkSize = datalength;

                // Function to get a range from the remote URL.
                var doXHR = (function(from, to) {
                    if (from > to) throw new Error("invalid range (" + from + ", " + to + ") or no bytes requested!");
                    if (to > datalength - 1) throw new Error("only " + datalength + " bytes available! programmer error!");

                    // TODO: Use mozResponseArrayBuffer, responseStream, etc. if available.
                    var xhr = new XMLHttpRequest();
                    xhr.open('GET', url, false);
                    if (datalength !== chunkSize) xhr.setRequestHeader("Range", "bytes=" + from + "-" + to);

                    // Some hints to the browser that we want binary data.
                    if (typeof Uint8Array != 'undefined') xhr.responseType = 'arraybuffer';
                    if (xhr.overrideMimeType) {
                        xhr.overrideMimeType('text/plain; charset=x-user-defined');
                    }

                    xhr.send(null);
                    if (!(xhr.status >= 200 && xhr.status < 300 || xhr.status === 304)) throw new Error("Couldn't load " + url + ". Status: " + xhr.status);
                    if (xhr.response !== undefined) {
                        return new Uint8Array(xhr.response || []);
                    } else {
                        return intArrayFromString(xhr.responseText || '', true);
                    }
                });
                var lazyArray = this;
                lazyArray.setDataGetter(function(chunkNum) {
                    var start = chunkNum * chunkSize;
                    var end = (chunkNum + 1) * chunkSize - 1; // including this byte
                    end = Math.min(end, datalength - 1); // if datalength-1 is selected, this is the last block
                    if (typeof(lazyArray.chunks[chunkNum]) === "undefined") {
                        lazyArray.chunks[chunkNum] = doXHR(start, end);
                    }
                    if (typeof(lazyArray.chunks[chunkNum]) === "undefined") throw new Error("doXHR failed!");
                    return lazyArray.chunks[chunkNum];
                });

                this._length = datalength;
                this._chunkSize = chunkSize;
                this.lengthKnown = true;
            }

            var lazyArray = new LazyUint8Array();
            Object.defineProperty(lazyArray, "length", {
                get: function() {
                    if (!this.lengthKnown) {
                        this.cacheLength();
                    }
                    return this._length;
                }
            });
            Object.defineProperty(lazyArray, "chunkSize", {
                get: function() {
                    if (!this.lengthKnown) {
                        this.cacheLength();
                    }
                    return this._chunkSize;
                }
            });

            var properties = {
                isDevice: false,
                contents: lazyArray
            };
        } else {
            var properties = {
                isDevice: false,
                url: url
            };
        }

        var node = FS.createFile(parent, name, properties, canRead, canWrite);
        // This is a total hack, but I want to get this lazy file code out of the
        // core of MEMFS. If we want to keep this lazy file concept I feel it should
        // be its own thin LAZYFS proxying calls to MEMFS.
        if (properties.contents) {
            node.contents = properties.contents;
        } else if (properties.url) {
            node.contents = null;
            node.url = properties.url;
        }
        // override each stream op with one that tries to force load the lazy file first
        var stream_ops = {};
        var keys = Object.keys(node.stream_ops);
        keys.forEach(function(key) {
            var fn = node.stream_ops[key];
            stream_ops[key] = function forceLoadLazyFile() {
                if (!FS.forceLoadFile(node)) {
                    throw new FS.ErrnoError(ERRNO_CODES.EIO);
                }
                return fn.apply(null, arguments);
            };
        });
        // use a custom read function
        stream_ops.read = function stream_ops_read(stream, buffer, offset, length, position) {
            if (!FS.forceLoadFile(node)) {
                throw new FS.ErrnoError(ERRNO_CODES.EIO);
            }
            var contents = stream.node.contents;
            if (position >= contents.length)
                return 0;
            var size = Math.min(contents.length - position, length);
            assert(size >= 0);
            if (contents.slice) { // normal array
                for (var i = 0; i < size; i++) {
                    buffer[offset + i] = contents[position + i];
                }
            } else {
                for (var i = 0; i < size; i++) { // LazyUint8Array from sync binary XHR
                    buffer[offset + i] = contents.get(position + i);
                }
            }
            return size;
        };
        node.stream_ops = stream_ops;
        return node;
    },
    createPreloadedFile: function(parent, name, url, canRead, canWrite, onload, onerror, dontCreateFile, canOwn) {
        Browser.init();
        // TODO we should allow people to just pass in a complete filename instead
        // of parent and name being that we just join them anyways
        var fullname = name ? PATH.resolve(PATH.join2(parent, name)) : parent;

        function processData(byteArray) {
            function finish(byteArray) {
                if (!dontCreateFile) {
                    FS.createDataFile(parent, name, byteArray, canRead, canWrite, canOwn);
                }
                if (onload) onload();
                removeRunDependency('cp ' + fullname);
            }
            var handled = false;
            Module['preloadPlugins'].forEach(function(plugin) {
                if (handled) return;
                if (plugin['canHandle'](fullname)) {
                    plugin['handle'](byteArray, fullname, finish, function() {
                        if (onerror) onerror();
                        removeRunDependency('cp ' + fullname);
                    });
                    handled = true;
                }
            });
            if (!handled) finish(byteArray);
        }
        addRunDependency('cp ' + fullname);
        if (typeof url == 'string') {
            Browser.asyncLoad(url, function(byteArray) {
                processData(byteArray);
            }, onerror);
        } else {
            processData(url);
        }
    },
    indexedDB: function() {
        return window.indexedDB || window.mozIndexedDB || window.webkitIndexedDB || window.msIndexedDB;
    },
    DB_NAME: function() {
        return 'EM_FS_' + window.location.pathname;
    },
    DB_VERSION: 20,
    DB_STORE_NAME: "FILE_DATA",
    saveFilesToDB: function(paths, onload, onerror) {
        onload = onload || function() {};
        onerror = onerror || function() {};
        var indexedDB = FS.indexedDB();
        try {
            var openRequest = indexedDB.open(FS.DB_NAME(), FS.DB_VERSION);
        } catch (e) {
            return onerror(e);
        }
        openRequest.onupgradeneeded = function openRequest_onupgradeneeded() {
            console.log('creating db');
            var db = openRequest.result;
            db.createObjectStore(FS.DB_STORE_NAME);
        };
        openRequest.onsuccess = function openRequest_onsuccess() {
            var db = openRequest.result;
            var transaction = db.transaction([FS.DB_STORE_NAME], 'readwrite');
            var files = transaction.objectStore(FS.DB_STORE_NAME);
            var ok = 0,
                fail = 0,
                total = paths.length;

            function finish() {
                if (fail == 0) onload();
                else onerror();
            }
            paths.forEach(function(path) {
                var putRequest = files.put(FS.analyzePath(path).object.contents, path);
                putRequest.onsuccess = function putRequest_onsuccess() {
                    ok++;
                    if (ok + fail == total) finish()
                };
                putRequest.onerror = function putRequest_onerror() {
                    fail++;
                    if (ok + fail == total) finish()
                };
            });
            transaction.onerror = onerror;
        };
        openRequest.onerror = onerror;
    },
    loadFilesFromDB: function(paths, onload, onerror) {
        onload = onload || function() {};
        onerror = onerror || function() {};
        var indexedDB = FS.indexedDB();
        try {
            var openRequest = indexedDB.open(FS.DB_NAME(), FS.DB_VERSION);
        } catch (e) {
            return onerror(e);
        }
        openRequest.onupgradeneeded = onerror; // no database to load from
        openRequest.onsuccess = function openRequest_onsuccess() {
            var db = openRequest.result;
            try {
                var transaction = db.transaction([FS.DB_STORE_NAME], 'readonly');
            } catch (e) {
                onerror(e);
                return;
            }
            var files = transaction.objectStore(FS.DB_STORE_NAME);
            var ok = 0,
                fail = 0,
                total = paths.length;

            function finish() {
                if (fail == 0) onload();
                else onerror();
            }
            paths.forEach(function(path) {
                var getRequest = files.get(path);
                getRequest.onsuccess = function getRequest_onsuccess() {
                    if (FS.analyzePath(path).exists) {
                        FS.unlink(path);
                    }
                    FS.createDataFile(PATH.dirname(path), PATH.basename(path), getRequest.result, true, true, true);
                    ok++;
                    if (ok + fail == total) finish();
                };
                getRequest.onerror = function getRequest_onerror() {
                    fail++;
                    if (ok + fail == total) finish()
                };
            });
            transaction.onerror = onerror;
        };
        openRequest.onerror = onerror;
    }
};




var _mkport = undefined;
var SOCKFS = {
    mount: function(mount) {
        return FS.createNode(null, '/', 16384 | 0777, 0);
    },
    createSocket: function(family, type, protocol) {
        var streaming = type == 1;
        if (protocol) {
            assert(streaming == (protocol == 6)); // if SOCK_STREAM, must be tcp
        }

        // create our internal socket structure
        var sock = {
            family: family,
            type: type,
            protocol: protocol,
            server: null,
            peers: {},
            pending: [],
            recv_queue: [],
            sock_ops: SOCKFS.websocket_sock_ops
        };

        // create the filesystem node to store the socket structure
        var name = SOCKFS.nextname();
        var node = FS.createNode(SOCKFS.root, name, 49152, 0);
        node.sock = sock;

        // and the wrapping stream that enables library functions such
        // as read and write to indirectly interact with the socket
        var stream = FS.createStream({
            path: name,
            node: node,
            flags: FS.modeStringToFlags('r+'),
            seekable: false,
            stream_ops: SOCKFS.stream_ops
        });

        // map the new stream to the socket structure (sockets have a 1:1
        // relationship with a stream)
        sock.stream = stream;

        return sock;
    },
    getSocket: function(fd) {
        var stream = FS.getStream(fd);
        if (!stream || !FS.isSocket(stream.node.mode)) {
            return null;
        }
        return stream.node.sock;
    },
    stream_ops: {
        poll: function(stream) {
            var sock = stream.node.sock;
            return sock.sock_ops.poll(sock);
        },
        ioctl: function(stream, request, varargs) {
            var sock = stream.node.sock;
            return sock.sock_ops.ioctl(sock, request, varargs);
        },
        read: function(stream, buffer, offset, length, position /* ignored */ ) {
            var sock = stream.node.sock;
            var msg = sock.sock_ops.recvmsg(sock, length);
            if (!msg) {
                // socket is closed
                return 0;
            }
            buffer.set(msg.buffer, offset);
            return msg.buffer.length;
        },
        write: function(stream, buffer, offset, length, position /* ignored */ ) {
            var sock = stream.node.sock;
            return sock.sock_ops.sendmsg(sock, buffer, offset, length);
        },
        close: function(stream) {
            var sock = stream.node.sock;
            sock.sock_ops.close(sock);
        }
    },
    nextname: function() {
        if (!SOCKFS.nextname.current) {
            SOCKFS.nextname.current = 0;
        }
        return 'socket[' + (SOCKFS.nextname.current++) + ']';
    },
    websocket_sock_ops: {
        createPeer: function(sock, addr, port) {
            var ws;

            if (typeof addr === 'object') {
                ws = addr;
                addr = null;
                port = null;
            }

            if (ws) {
                // for sockets that've already connected (e.g. we're the server)
                // we can inspect the _socket property for the address
                if (ws._socket) {
                    addr = ws._socket.remoteAddress;
                    port = ws._socket.remotePort;
                }
                // if we're just now initializing a connection to the remote,
                // inspect the url property
                else {
                    var result = /ws[s]?:\/\/([^:]+):(\d+)/.exec(ws.url);
                    if (!result) {
                        throw new Error('WebSocket URL must be in the format ws(s)://address:port');
                    }
                    addr = result[1];
                    port = parseInt(result[2], 10);
                }
            } else {
                // create the actual websocket object and connect
                try {
                    var url = 'ws://' + addr + ':' + port;
                    // the node ws library API is slightly different than the browser's
                    var opts = ENVIRONMENT_IS_NODE ? {
                        headers: {
                            'websocket-protocol': ['binary']
                        }
                    } : ['binary'];
                    // If node we use the ws library.
                    var WebSocket = ENVIRONMENT_IS_NODE ? require('ws') : window['WebSocket'];
                    ws = new WebSocket(url, opts);
                    ws.binaryType = 'arraybuffer';
                } catch (e) {
                    throw new FS.ErrnoError(ERRNO_CODES.EHOSTUNREACH);
                }
            }


            var peer = {
                addr: addr,
                port: port,
                socket: ws,
                dgram_send_queue: []
            };

            SOCKFS.websocket_sock_ops.addPeer(sock, peer);
            SOCKFS.websocket_sock_ops.handlePeerEvents(sock, peer);

            // if this is a bound dgram socket, send the port number first to allow
            // us to override the ephemeral port reported to us by remotePort on the
            // remote end.
            if (sock.type === 2 && typeof sock.sport !== 'undefined') {
                peer.dgram_send_queue.push(new Uint8Array([
                    255, 255, 255, 255,
                    'p'.charCodeAt(0), 'o'.charCodeAt(0), 'r'.charCodeAt(0), 't'.charCodeAt(0), ((sock.sport & 0xff00) >> 8), (sock.sport & 0xff)
                ]));
            }

            return peer;
        },
        getPeer: function(sock, addr, port) {
            return sock.peers[addr + ':' + port];
        },
        addPeer: function(sock, peer) {
            sock.peers[peer.addr + ':' + peer.port] = peer;
        },
        removePeer: function(sock, peer) {
            delete sock.peers[peer.addr + ':' + peer.port];
        },
        handlePeerEvents: function(sock, peer) {
            var first = true;

            var handleOpen = function() {
                try {
                    var queued = peer.dgram_send_queue.shift();
                    while (queued) {
                        peer.socket.send(queued);
                        queued = peer.dgram_send_queue.shift();
                    }
                } catch (e) {
                    // not much we can do here in the way of proper error handling as we've already
                    // lied and said this data was sent. shut it down.
                    peer.socket.close();
                }
            };

            function handleMessage(data) {
                assert(typeof data !== 'string' && data.byteLength !== undefined); // must receive an ArrayBuffer
                data = new Uint8Array(data); // make a typed array view on the array buffer


                // if this is the port message, override the peer's port with it
                var wasfirst = first;
                first = false;
                if (wasfirst &&
                    data.length === 10 &&
                    data[0] === 255 && data[1] === 255 && data[2] === 255 && data[3] === 255 &&
                    data[4] === 'p'.charCodeAt(0) && data[5] === 'o'.charCodeAt(0) && data[6] === 'r'.charCodeAt(0) && data[7] === 't'.charCodeAt(0)) {
                    // update the peer's port and it's key in the peer map
                    var newport = ((data[8] << 8) | data[9]);
                    SOCKFS.websocket_sock_ops.removePeer(sock, peer);
                    peer.port = newport;
                    SOCKFS.websocket_sock_ops.addPeer(sock, peer);
                    return;
                }

                sock.recv_queue.push({
                    addr: peer.addr,
                    port: peer.port,
                    data: data
                });
            };

            if (ENVIRONMENT_IS_NODE) {
                peer.socket.on('open', handleOpen);
                peer.socket.on('message', function(data, flags) {
                    if (!flags.binary) {
                        return;
                    }
                    handleMessage((new Uint8Array(data)).buffer); // copy from node Buffer -> ArrayBuffer
                });
                peer.socket.on('error', function() {
                    // don't throw
                });
            } else {
                peer.socket.onopen = handleOpen;
                peer.socket.onmessage = function peer_socket_onmessage(event) {
                    handleMessage(event.data);
                };
            }
        },
        poll: function(sock) {
            if (sock.type === 1 && sock.server) {
                // listen sockets should only say they're available for reading
                // if there are pending clients.
                return sock.pending.length ? (64 | 1) : 0;
            }

            var mask = 0;
            var dest = sock.type === 1 ? // we only care about the socket state for connection-based sockets
                SOCKFS.websocket_sock_ops.getPeer(sock, sock.daddr, sock.dport) :
                null;

            if (sock.recv_queue.length ||
                !dest || // connection-less sockets are always ready to read
                (dest && dest.socket.readyState === dest.socket.CLOSING) ||
                (dest && dest.socket.readyState === dest.socket.CLOSED)) { // let recv return 0 once closed
                mask |= (64 | 1);
            }

            if (!dest || // connection-less sockets are always ready to write
                (dest && dest.socket.readyState === dest.socket.OPEN)) {
                mask |= 4;
            }

            if ((dest && dest.socket.readyState === dest.socket.CLOSING) ||
                (dest && dest.socket.readyState === dest.socket.CLOSED)) {
                mask |= 16;
            }

            return mask;
        },
        ioctl: function(sock, request, arg) {
            switch (request) {
                case 21531:
                    var bytes = 0;
                    if (sock.recv_queue.length) {
                        bytes = sock.recv_queue[0].data.length;
                    }
                    HEAP32[((arg) >> 2)] = bytes;
                    return 0;
                default:
                    return ERRNO_CODES.EINVAL;
            }
        },
        close: function(sock) {
            // if we've spawned a listen server, close it
            if (sock.server) {
                try {
                    sock.server.close();
                } catch (e) {}
                sock.server = null;
            }
            // close any peer connections
            var peers = Object.keys(sock.peers);
            for (var i = 0; i < peers.length; i++) {
                var peer = sock.peers[peers[i]];
                try {
                    peer.socket.close();
                } catch (e) {}
                SOCKFS.websocket_sock_ops.removePeer(sock, peer);
            }
            return 0;
        },
        bind: function(sock, addr, port) {
            if (typeof sock.saddr !== 'undefined' || typeof sock.sport !== 'undefined') {
                throw new FS.ErrnoError(ERRNO_CODES.EINVAL); // already bound
            }
            sock.saddr = addr;
            sock.sport = port || _mkport();
            // in order to emulate dgram sockets, we need to launch a listen server when
            // binding on a connection-less socket
            // note: this is only required on the server side
            if (sock.type === 2) {
                // close the existing server if it exists
                if (sock.server) {
                    sock.server.close();
                    sock.server = null;
                }
                // swallow error operation not supported error that occurs when binding in the
                // browser where this isn't supported
                try {
                    sock.sock_ops.listen(sock, 0);
                } catch (e) {
                    if (!(e instanceof FS.ErrnoError)) throw e;
                    if (e.errno !== ERRNO_CODES.EOPNOTSUPP) throw e;
                }
            }
        },
        connect: function(sock, addr, port) {
            if (sock.server) {
                throw new FS.ErrnoError(ERRNO_CODS.EOPNOTSUPP);
            }

            // TODO autobind
            // if (!sock.addr && sock.type == 2) {
            // }

            // early out if we're already connected / in the middle of connecting
            if (typeof sock.daddr !== 'undefined' && typeof sock.dport !== 'undefined') {
                var dest = SOCKFS.websocket_sock_ops.getPeer(sock, sock.daddr, sock.dport);
                if (dest) {
                    if (dest.socket.readyState === dest.socket.CONNECTING) {
                        throw new FS.ErrnoError(ERRNO_CODES.EALREADY);
                    } else {
                        throw new FS.ErrnoError(ERRNO_CODES.EISCONN);
                    }
                }
            }

            // add the socket to our peer list and set our
            // destination address / port to match
            var peer = SOCKFS.websocket_sock_ops.createPeer(sock, addr, port);
            sock.daddr = peer.addr;
            sock.dport = peer.port;

            // always "fail" in non-blocking mode
            throw new FS.ErrnoError(ERRNO_CODES.EINPROGRESS);
        },
        listen: function(sock, backlog) {
            if (!ENVIRONMENT_IS_NODE) {
                throw new FS.ErrnoError(ERRNO_CODES.EOPNOTSUPP);
            }
            if (sock.server) {
                throw new FS.ErrnoError(ERRNO_CODES.EINVAL); // already listening
            }
            var WebSocketServer = require('ws').Server;
            var host = sock.saddr;
            sock.server = new WebSocketServer({
                host: host,
                port: sock.sport
                    // TODO support backlog
            });

            sock.server.on('connection', function(ws) {
                if (sock.type === 1) {
                    var newsock = SOCKFS.createSocket(sock.family, sock.type, sock.protocol);

                    // create a peer on the new socket
                    var peer = SOCKFS.websocket_sock_ops.createPeer(newsock, ws);
                    newsock.daddr = peer.addr;
                    newsock.dport = peer.port;

                    // push to queue for accept to pick up
                    sock.pending.push(newsock);
                } else {
                    // create a peer on the listen socket so calling sendto
                    // with the listen socket and an address will resolve
                    // to the correct client
                    SOCKFS.websocket_sock_ops.createPeer(sock, ws);
                }
            });
            sock.server.on('closed', function() {
                sock.server = null;
            });
            sock.server.on('error', function() {
                // don't throw
            });
        },
        accept: function(listensock) {
            if (!listensock.server) {
                throw new FS.ErrnoError(ERRNO_CODES.EINVAL);
            }
            var newsock = listensock.pending.shift();
            newsock.stream.flags = listensock.stream.flags;
            return newsock;
        },
        getname: function(sock, peer) {
            var addr, port;
            if (peer) {
                if (sock.daddr === undefined || sock.dport === undefined) {
                    throw new FS.ErrnoError(ERRNO_CODES.ENOTCONN);
                }
                addr = sock.daddr;
                port = sock.dport;
            } else {
                // TODO saddr and sport will be set for bind()'d UDP sockets, but what
                // should we be returning for TCP sockets that've been connect()'d?
                addr = sock.saddr || 0;
                port = sock.sport || 0;
            }
            return {
                addr: addr,
                port: port
            };
        },
        sendmsg: function(sock, buffer, offset, length, addr, port) {
            if (sock.type === 2) {
                // connection-less sockets will honor the message address,
                // and otherwise fall back to the bound destination address
                if (addr === undefined || port === undefined) {
                    addr = sock.daddr;
                    port = sock.dport;
                }
                // if there was no address to fall back to, error out
                if (addr === undefined || port === undefined) {
                    throw new FS.ErrnoError(ERRNO_CODES.EDESTADDRREQ);
                }
            } else {
                // connection-based sockets will only use the bound
                addr = sock.daddr;
                port = sock.dport;
            }

            // find the peer for the destination address
            var dest = SOCKFS.websocket_sock_ops.getPeer(sock, addr, port);

            // early out if not connected with a connection-based socket
            if (sock.type === 1) {
                if (!dest || dest.socket.readyState === dest.socket.CLOSING || dest.socket.readyState === dest.socket.CLOSED) {
                    throw new FS.ErrnoError(ERRNO_CODES.ENOTCONN);
                } else if (dest.socket.readyState === dest.socket.CONNECTING) {
                    throw new FS.ErrnoError(ERRNO_CODES.EAGAIN);
                }
            }

            // create a copy of the incoming data to send, as the WebSocket API
            // doesn't work entirely with an ArrayBufferView, it'll just send
            // the entire underlying buffer
            var data;
            if (buffer instanceof Array || buffer instanceof ArrayBuffer) {
                data = buffer.slice(offset, offset + length);
            } else { // ArrayBufferView
                data = buffer.buffer.slice(buffer.byteOffset + offset, buffer.byteOffset + offset + length);
            }

            // if we're emulating a connection-less dgram socket and don't have
            // a cached connection, queue the buffer to send upon connect and
            // lie, saying the data was sent now.
            if (sock.type === 2) {
                if (!dest || dest.socket.readyState !== dest.socket.OPEN) {
                    // if we're not connected, open a new connection
                    if (!dest || dest.socket.readyState === dest.socket.CLOSING || dest.socket.readyState === dest.socket.CLOSED) {
                        dest = SOCKFS.websocket_sock_ops.createPeer(sock, addr, port);
                    }
                    dest.dgram_send_queue.push(data);
                    return length;
                }
            }

            try {
                // send the actual data
                dest.socket.send(data);
                return length;
            } catch (e) {
                throw new FS.ErrnoError(ERRNO_CODES.EINVAL);
            }
        },
        recvmsg: function(sock, length) {
            // http://pubs.opengroup.org/onlinepubs/7908799/xns/recvmsg.html
            if (sock.type === 1 && sock.server) {
                // tcp servers should not be recv()'ing on the listen socket
                throw new FS.ErrnoError(ERRNO_CODES.ENOTCONN);
            }

            var queued = sock.recv_queue.shift();
            if (!queued) {
                if (sock.type === 1) {
                    var dest = SOCKFS.websocket_sock_ops.getPeer(sock, sock.daddr, sock.dport);

                    if (!dest) {
                        // if we have a destination address but are not connected, error out
                        throw new FS.ErrnoError(ERRNO_CODES.ENOTCONN);
                    } else if (dest.socket.readyState === dest.socket.CLOSING || dest.socket.readyState === dest.socket.CLOSED) {
                        // return null if the socket has closed
                        return null;
                    } else {
                        // else, our socket is in a valid state but truly has nothing available
                        throw new FS.ErrnoError(ERRNO_CODES.EAGAIN);
                    }
                } else {
                    throw new FS.ErrnoError(ERRNO_CODES.EAGAIN);
                }
            }

            // queued.data will be an ArrayBuffer if it's unadulterated, but if it's
            // requeued TCP data it'll be an ArrayBufferView
            var queuedLength = queued.data.byteLength || queued.data.length;
            var queuedOffset = queued.data.byteOffset || 0;
            var queuedBuffer = queued.data.buffer || queued.data;
            var bytesRead = Math.min(length, queuedLength);
            var res = {
                buffer: new Uint8Array(queuedBuffer, queuedOffset, bytesRead),
                addr: queued.addr,
                port: queued.port
            };


            // push back any unread data for TCP connections
            if (sock.type === 1 && bytesRead < queuedLength) {
                var bytesRemaining = queuedLength - bytesRead;
                queued.data = new Uint8Array(queuedBuffer, queuedOffset + bytesRead, bytesRemaining);
                sock.recv_queue.unshift(queued);
            }

            return res;
        }
    }
};

function _send(fd, buf, len, flags) {
    var sock = SOCKFS.getSocket(fd);
    if (!sock) {
        ___setErrNo(ERRNO_CODES.EBADF);
        return -1;
    }
    // TODO honor flags
    return _write(fd, buf, len);
}

function _pwrite(fildes, buf, nbyte, offset) {
    // ssize_t pwrite(int fildes, const void *buf, size_t nbyte, off_t offset);
    // http://pubs.opengroup.org/onlinepubs/000095399/functions/write.html
    var stream = FS.getStream(fildes);
    if (!stream) {
        ___setErrNo(ERRNO_CODES.EBADF);
        return -1;
    }
    try {
        var slab = HEAP8;
        return FS.write(stream, slab, buf, nbyte, offset);
    } catch (e) {
        FS.handleFSError(e);
        return -1;
    }
}

function _write(fildes, buf, nbyte) {
    // ssize_t write(int fildes, const void *buf, size_t nbyte);
    // http://pubs.opengroup.org/onlinepubs/000095399/functions/write.html
    var stream = FS.getStream(fildes);
    if (!stream) {
        ___setErrNo(ERRNO_CODES.EBADF);
        return -1;
    }


    try {
        var slab = HEAP8;
        return FS.write(stream, slab, buf, nbyte);
    } catch (e) {
        FS.handleFSError(e);
        return -1;
    }
}

function _fwrite(ptr, size, nitems, stream) {
    // size_t fwrite(const void *restrict ptr, size_t size, size_t nitems, FILE *restrict stream);
    // http://pubs.opengroup.org/onlinepubs/000095399/functions/fwrite.html
    var bytesToWrite = nitems * size;
    if (bytesToWrite == 0) return 0;
    var bytesWritten = _write(stream, ptr, bytesToWrite);
    if (bytesWritten == -1) {
        var streamObj = FS.getStream(stream);
        if (streamObj) streamObj.error = true;
        return 0;
    } else {
        return Math.floor(bytesWritten / size);
    }
}



Module["_strlen"] = _strlen;

function __reallyNegative(x) {
    return x < 0 || (x === 0 && (1 / x) === -Infinity);
}

function __formatString(format, varargs) {
    var textIndex = format;
    var argIndex = 0;

    function getNextArg(type) {
        // NOTE: Explicitly ignoring type safety. Otherwise this fails:
        //       int x = 4; printf("%c\n", (char)x);
        var ret;
        if (type === 'double') {
            ret = HEAPF64[(((varargs) + (argIndex)) >> 3)];
        } else if (type == 'i64') {
            ret = [HEAP32[(((varargs) + (argIndex)) >> 2)],
                HEAP32[(((varargs) + (argIndex + 8)) >> 2)]
            ];
            argIndex += 8; // each 32-bit chunk is in a 64-bit block

        } else {
            type = 'i32'; // varargs are always i32, i64, or double
            ret = HEAP32[(((varargs) + (argIndex)) >> 2)];
        }
        argIndex += Math.max(Runtime.getNativeFieldSize(type), Runtime.getAlignSize(type, null, true));
        return ret;
    }

    var ret = [];
    var curr, next, currArg;
    while (1) {
        var startTextIndex = textIndex;
        curr = HEAP8[(textIndex)];
        if (curr === 0) break;
        next = HEAP8[((textIndex + 1) | 0)];
        if (curr == 37) {
            // Handle flags.
            var flagAlwaysSigned = false;
            var flagLeftAlign = false;
            var flagAlternative = false;
            var flagZeroPad = false;
            var flagPadSign = false;
            flagsLoop: while (1) {
                switch (next) {
                    case 43:
                        flagAlwaysSigned = true;
                        break;
                    case 45:
                        flagLeftAlign = true;
                        break;
                    case 35:
                        flagAlternative = true;
                        break;
                    case 48:
                        if (flagZeroPad) {
                            break flagsLoop;
                        } else {
                            flagZeroPad = true;
                            break;
                        }
                    case 32:
                        flagPadSign = true;
                        break;
                    default:
                        break flagsLoop;
                }
                textIndex++;
                next = HEAP8[((textIndex + 1) | 0)];
            }

            // Handle width.
            var width = 0;
            if (next == 42) {
                width = getNextArg('i32');
                textIndex++;
                next = HEAP8[((textIndex + 1) | 0)];
            } else {
                while (next >= 48 && next <= 57) {
                    width = width * 10 + (next - 48);
                    textIndex++;
                    next = HEAP8[((textIndex + 1) | 0)];
                }
            }

            // Handle precision.
            var precisionSet = false,
                precision = -1;
            if (next == 46) {
                precision = 0;
                precisionSet = true;
                textIndex++;
                next = HEAP8[((textIndex + 1) | 0)];
                if (next == 42) {
                    precision = getNextArg('i32');
                    textIndex++;
                } else {
                    while (1) {
                        var precisionChr = HEAP8[((textIndex + 1) | 0)];
                        if (precisionChr < 48 ||
                            precisionChr > 57) break;
                        precision = precision * 10 + (precisionChr - 48);
                        textIndex++;
                    }
                }
                next = HEAP8[((textIndex + 1) | 0)];
            }
            if (precision === -1) {
                precision = 6; // Standard default.
                precisionSet = false;
            }

            // Handle integer sizes. WARNING: These assume a 32-bit architecture!
            var argSize;
            switch (String.fromCharCode(next)) {
                case 'h':
                    var nextNext = HEAP8[((textIndex + 2) | 0)];
                    if (nextNext == 104) {
                        textIndex++;
                        argSize = 1; // char (actually i32 in varargs)
                    } else {
                        argSize = 2; // short (actually i32 in varargs)
                    }
                    break;
                case 'l':
                    var nextNext = HEAP8[((textIndex + 2) | 0)];
                    if (nextNext == 108) {
                        textIndex++;
                        argSize = 8; // long long
                    } else {
                        argSize = 4; // long
                    }
                    break;
                case 'L': // long long
                case 'q': // int64_t
                case 'j': // intmax_t
                    argSize = 8;
                    break;
                case 'z': // size_t
                case 't': // ptrdiff_t
                case 'I': // signed ptrdiff_t or unsigned size_t
                    argSize = 4;
                    break;
                default:
                    argSize = null;
            }
            if (argSize) textIndex++;
            next = HEAP8[((textIndex + 1) | 0)];

            // Handle type specifier.
            switch (String.fromCharCode(next)) {
                case 'd':
                case 'i':
                case 'u':
                case 'o':
                case 'x':
                case 'X':
                case 'p':
                    {
                        // Integer.
                        var signed = next == 100 || next == 105;
                        argSize = argSize || 4;
                        var currArg = getNextArg('i' + (argSize * 8));
                        var origArg = currArg;
                        var argText;
                        // Flatten i64-1 [low, high] into a (slightly rounded) double
                        if (argSize == 8) {
                            currArg = Runtime.makeBigInt(currArg[0], currArg[1], next == 117);
                        }
                        // Truncate to requested size.
                        if (argSize <= 4) {
                            var limit = Math.pow(256, argSize) - 1;
                            currArg = (signed ? reSign : unSign)(currArg & limit, argSize * 8);
                        }
                        // Format the number.
                        var currAbsArg = Math.abs(currArg);
                        var prefix = '';
                        if (next == 100 || next == 105) {
                            if (argSize == 8 && i64Math) argText = i64Math.stringify(origArg[0], origArg[1], null);
                            else
                                argText = reSign(currArg, 8 * argSize, 1).toString(10);
                        } else if (next == 117) {
                            if (argSize == 8 && i64Math) argText = i64Math.stringify(origArg[0], origArg[1], true);
                            else
                                argText = unSign(currArg, 8 * argSize, 1).toString(10);
                            currArg = Math.abs(currArg);
                        } else if (next == 111) {
                            argText = (flagAlternative ? '0' : '') + currAbsArg.toString(8);
                        } else if (next == 120 || next == 88) {
                            prefix = (flagAlternative && currArg != 0) ? '0x' : '';
                            if (argSize == 8 && i64Math) {
                                if (origArg[1]) {
                                    argText = (origArg[1] >>> 0).toString(16);
                                    var lower = (origArg[0] >>> 0).toString(16);
                                    while (lower.length < 8) lower = '0' + lower;
                                    argText += lower;
                                } else {
                                    argText = (origArg[0] >>> 0).toString(16);
                                }
                            } else
                            if (currArg < 0) {
                                // Represent negative numbers in hex as 2's complement.
                                currArg = -currArg;
                                argText = (currAbsArg - 1).toString(16);
                                var buffer = [];
                                for (var i = 0; i < argText.length; i++) {
                                    buffer.push((0xF - parseInt(argText[i], 16)).toString(16));
                                }
                                argText = buffer.join('');
                                while (argText.length < argSize * 2) argText = 'f' + argText;
                            } else {
                                argText = currAbsArg.toString(16);
                            }
                            if (next == 88) {
                                prefix = prefix.toUpperCase();
                                argText = argText.toUpperCase();
                            }
                        } else if (next == 112) {
                            if (currAbsArg === 0) {
                                argText = '(nil)';
                            } else {
                                prefix = '0x';
                                argText = currAbsArg.toString(16);
                            }
                        }
                        if (precisionSet) {
                            while (argText.length < precision) {
                                argText = '0' + argText;
                            }
                        }

                        // Add sign if needed
                        if (currArg >= 0) {
                            if (flagAlwaysSigned) {
                                prefix = '+' + prefix;
                            } else if (flagPadSign) {
                                prefix = ' ' + prefix;
                            }
                        }

                        // Move sign to prefix so we zero-pad after the sign
                        if (argText.charAt(0) == '-') {
                            prefix = '-' + prefix;
                            argText = argText.substr(1);
                        }

                        // Add padding.
                        while (prefix.length + argText.length < width) {
                            if (flagLeftAlign) {
                                argText += ' ';
                            } else {
                                if (flagZeroPad) {
                                    argText = '0' + argText;
                                } else {
                                    prefix = ' ' + prefix;
                                }
                            }
                        }

                        // Insert the result into the buffer.
                        argText = prefix + argText;
                        argText.split('').forEach(function(chr) {
                            ret.push(chr.charCodeAt(0));
                        });
                        break;
                    }
                case 'f':
                case 'F':
                case 'e':
                case 'E':
                case 'g':
                case 'G':
                    {
                        // Float.
                        var currArg = getNextArg('double');
                        var argText;
                        if (isNaN(currArg)) {
                            argText = 'nan';
                            flagZeroPad = false;
                        } else if (!isFinite(currArg)) {
                            argText = (currArg < 0 ? '-' : '') + 'inf';
                            flagZeroPad = false;
                        } else {
                            var isGeneral = false;
                            var effectivePrecision = Math.min(precision, 20);

                            // Convert g/G to f/F or e/E, as per:
                            // http://pubs.opengroup.org/onlinepubs/9699919799/functions/printf.html
                            if (next == 103 || next == 71) {
                                isGeneral = true;
                                precision = precision || 1;
                                var exponent = parseInt(currArg.toExponential(effectivePrecision).split('e')[1], 10);
                                if (precision > exponent && exponent >= -4) {
                                    next = ((next == 103) ? 'f' : 'F').charCodeAt(0);
                                    precision -= exponent + 1;
                                } else {
                                    next = ((next == 103) ? 'e' : 'E').charCodeAt(0);
                                    precision--;
                                }
                                effectivePrecision = Math.min(precision, 20);
                            }

                            if (next == 101 || next == 69) {
                                argText = currArg.toExponential(effectivePrecision);
                                // Make sure the exponent has at least 2 digits.
                                if (/[eE][-+]\d$/.test(argText)) {
                                    argText = argText.slice(0, -1) + '0' + argText.slice(-1);
                                }
                            } else if (next == 102 || next == 70) {
                                argText = currArg.toFixed(effectivePrecision);
                                if (currArg === 0 && __reallyNegative(currArg)) {
                                    argText = '-' + argText;
                                }
                            }

                            var parts = argText.split('e');
                            if (isGeneral && !flagAlternative) {
                                // Discard trailing zeros and periods.
                                while (parts[0].length > 1 && parts[0].indexOf('.') != -1 &&
                                    (parts[0].slice(-1) == '0' || parts[0].slice(-1) == '.')) {
                                    parts[0] = parts[0].slice(0, -1);
                                }
                            } else {
                                // Make sure we have a period in alternative mode.
                                if (flagAlternative && argText.indexOf('.') == -1) parts[0] += '.';
                                // Zero pad until required precision.
                                while (precision > effectivePrecision++) parts[0] += '0';
                            }
                            argText = parts[0] + (parts.length > 1 ? 'e' + parts[1] : '');

                            // Capitalize 'E' if needed.
                            if (next == 69) argText = argText.toUpperCase();

                            // Add sign.
                            if (currArg >= 0) {
                                if (flagAlwaysSigned) {
                                    argText = '+' + argText;
                                } else if (flagPadSign) {
                                    argText = ' ' + argText;
                                }
                            }
                        }

                        // Add padding.
                        while (argText.length < width) {
                            if (flagLeftAlign) {
                                argText += ' ';
                            } else {
                                if (flagZeroPad && (argText[0] == '-' || argText[0] == '+')) {
                                    argText = argText[0] + '0' + argText.slice(1);
                                } else {
                                    argText = (flagZeroPad ? '0' : ' ') + argText;
                                }
                            }
                        }

                        // Adjust case.
                        if (next < 97) argText = argText.toUpperCase();

                        // Insert the result into the buffer.
                        argText.split('').forEach(function(chr) {
                            ret.push(chr.charCodeAt(0));
                        });
                        break;
                    }
                case 's':
                    {
                        // String.
                        var arg = getNextArg('i8*');
                        var argLength = arg ? _strlen(arg) : '(null)'.length;
                        if (precisionSet) argLength = Math.min(argLength, precision);
                        if (!flagLeftAlign) {
                            while (argLength < width--) {
                                ret.push(32);
                            }
                        }
                        if (arg) {
                            for (var i = 0; i < argLength; i++) {
                                ret.push(HEAPU8[((arg++) | 0)]);
                            }
                        } else {
                            ret = ret.concat(intArrayFromString('(null)'.substr(0, argLength), true));
                        }
                        if (flagLeftAlign) {
                            while (argLength < width--) {
                                ret.push(32);
                            }
                        }
                        break;
                    }
                case 'c':
                    {
                        // Character.
                        if (flagLeftAlign) ret.push(getNextArg('i8'));
                        while (--width > 0) {
                            ret.push(32);
                        }
                        if (!flagLeftAlign) ret.push(getNextArg('i8'));
                        break;
                    }
                case 'n':
                    {
                        // Write the length written so far to the next parameter.
                        var ptr = getNextArg('i32*');
                        HEAP32[((ptr) >> 2)] = ret.length;
                        break;
                    }
                case '%':
                    {
                        // Literal percent sign.
                        ret.push(curr);
                        break;
                    }
                default:
                    {
                        // Unknown specifiers remain untouched.
                        for (var i = startTextIndex; i < textIndex + 2; i++) {
                            ret.push(HEAP8[(i)]);
                        }
                    }
            }
            textIndex += 2;
            // TODO: Support a/A (hex float) and m (last error) specifiers.
            // TODO: Support %1${specifier} for arg selection.
        } else {
            ret.push(curr);
            textIndex += 1;
        }
    }
    return ret;
}

function _fprintf(stream, format, varargs) {
    // int fprintf(FILE *restrict stream, const char *restrict format, ...);
    // http://pubs.opengroup.org/onlinepubs/000095399/functions/printf.html
    var result = __formatString(format, varargs);
    var stack = Runtime.stackSave();
    var ret = _fwrite(allocate(result, 'i8', ALLOC_STACK), 1, result.length, stream);
    Runtime.stackRestore(stack);
    return ret;
}

function _printf(format, varargs) {
    // int printf(const char *restrict format, ...);
    // http://pubs.opengroup.org/onlinepubs/000095399/functions/printf.html
    var stdout = HEAP32[((_stdout) >> 2)];
    return _fprintf(stdout, format, varargs);
}

var _sqrtf = Math_sqrt;

var _fabsf = Math_abs;


function _fputs(s, stream) {
    // int fputs(const char *restrict s, FILE *restrict stream);
    // http://pubs.opengroup.org/onlinepubs/000095399/functions/fputs.html
    return _write(stream, s, _strlen(s));
}

function _fputc(c, stream) {
    // int fputc(int c, FILE *stream);
    // http://pubs.opengroup.org/onlinepubs/000095399/functions/fputc.html
    var chr = unSign(c & 0xFF);
    HEAP8[((_fputc.ret) | 0)] = chr;
    var ret = _write(stream, _fputc.ret, 1);
    if (ret == -1) {
        var streamObj = FS.getStream(stream);
        if (streamObj) streamObj.error = true;
        return -1;
    } else {
        return chr;
    }
}

function _puts(s) {
    // int puts(const char *s);
    // http://pubs.opengroup.org/onlinepubs/000095399/functions/puts.html
    // NOTE: puts() always writes an extra newline.
    var stdout = HEAP32[((_stdout) >> 2)];
    var ret = _fputs(s, stdout);
    if (ret < 0) {
        return ret;
    } else {
        var newlineRet = _fputc(10, stdout);
        return (newlineRet < 0) ? -1 : ret + 1;
    }
}

function _abort() {
    Module['abort']();
}

function ___errno_location() {
    return ___errno_state;
}

function _sbrk(bytes) {
    // Implement a Linux-like 'memory area' for our 'process'.
    // Changes the size of the memory area by |bytes|; returns the
    // address of the previous top ('break') of the memory area
    // We control the "dynamic" memory - DYNAMIC_BASE to DYNAMICTOP
    var self = _sbrk;
    if (!self.called) {
        DYNAMICTOP = alignMemoryPage(DYNAMICTOP); // make sure we start out aligned
        self.called = true;
        assert(Runtime.dynamicAlloc);
        self.alloc = Runtime.dynamicAlloc;
        Runtime.dynamicAlloc = function() {
            abort('cannot dynamically allocate, sbrk now has control')
        };
    }
    var ret = DYNAMICTOP;
    if (bytes != 0) self.alloc(bytes);
    return ret; // Previous break location.
}

function _sysconf(name) {
    // long sysconf(int name);
    // http://pubs.opengroup.org/onlinepubs/009695399/functions/sysconf.html
    switch (name) {
        case 30:
            return PAGE_SIZE;
        case 132:
        case 133:
        case 12:
        case 137:
        case 138:
        case 15:
        case 235:
        case 16:
        case 17:
        case 18:
        case 19:
        case 20:
        case 149:
        case 13:
        case 10:
        case 236:
        case 153:
        case 9:
        case 21:
        case 22:
        case 159:
        case 154:
        case 14:
        case 77:
        case 78:
        case 139:
        case 80:
        case 81:
        case 79:
        case 82:
        case 68:
        case 67:
        case 164:
        case 11:
        case 29:
        case 47:
        case 48:
        case 95:
        case 52:
        case 51:
        case 46:
            return 200809;
        case 27:
        case 246:
        case 127:
        case 128:
        case 23:
        case 24:
        case 160:
        case 161:
        case 181:
        case 182:
        case 242:
        case 183:
        case 184:
        case 243:
        case 244:
        case 245:
        case 165:
        case 178:
        case 179:
        case 49:
        case 50:
        case 168:
        case 169:
        case 175:
        case 170:
        case 171:
        case 172:
        case 97:
        case 76:
        case 32:
        case 173:
        case 35:
            return -1;
        case 176:
        case 177:
        case 7:
        case 155:
        case 8:
        case 157:
        case 125:
        case 126:
        case 92:
        case 93:
        case 129:
        case 130:
        case 131:
        case 94:
        case 91:
            return 1;
        case 74:
        case 60:
        case 69:
        case 70:
        case 4:
            return 1024;
        case 31:
        case 42:
        case 72:
            return 32;
        case 87:
        case 26:
        case 33:
            return 2147483647;
        case 34:
        case 1:
            return 47839;
        case 38:
        case 36:
            return 99;
        case 43:
        case 37:
            return 2048;
        case 0:
            return 2097152;
        case 3:
            return 65536;
        case 28:
            return 32768;
        case 44:
            return 32767;
        case 75:
            return 16384;
        case 39:
            return 1000;
        case 89:
            return 700;
        case 71:
            return 256;
        case 40:
            return 255;
        case 2:
            return 100;
        case 180:
            return 64;
        case 25:
            return 20;
        case 5:
            return 16;
        case 6:
            return 6;
        case 73:
            return 4;
        case 84:
            return 1;
    }
    ___setErrNo(ERRNO_CODES.EINVAL);
    return -1;
}

function _time(ptr) {
    var ret = Math.floor(Date.now() / 1000);
    if (ptr) {
        HEAP32[((ptr) >> 2)] = ret;
    }
    return ret;
}



Module["_memset"] = _memset;




var Browser = {
    mainLoop: {
        scheduler: null,
        shouldPause: false,
        paused: false,
        queue: [],
        pause: function() {
            Browser.mainLoop.shouldPause = true;
        },
        resume: function() {
            if (Browser.mainLoop.paused) {
                Browser.mainLoop.paused = false;
                Browser.mainLoop.scheduler();
            }
            Browser.mainLoop.shouldPause = false;
        },
        updateStatus: function() {
            if (Module['setStatus']) {
                var message = Module['statusMessage'] || 'Please wait...';
                var remaining = Browser.mainLoop.remainingBlockers;
                var expected = Browser.mainLoop.expectedBlockers;
                if (remaining) {
                    if (remaining < expected) {
                        Module['setStatus'](message + ' (' + (expected - remaining) + '/' + expected + ')');
                    } else {
                        Module['setStatus'](message);
                    }
                } else {
                    Module['setStatus']('');
                }
            }
        }
    },
    isFullScreen: false,
    pointerLock: false,
    moduleContextCreatedCallbacks: [],
    workers: [],
    init: function() {
        if (!Module["preloadPlugins"]) Module["preloadPlugins"] = []; // needs to exist even in workers

        if (Browser.initted || ENVIRONMENT_IS_WORKER) return;
        Browser.initted = true;

        try {
            new Blob();
            Browser.hasBlobConstructor = true;
        } catch (e) {
            Browser.hasBlobConstructor = false;
            console.log("warning: no blob constructor, cannot create blobs with mimetypes");
        }
        Browser.BlobBuilder = typeof MozBlobBuilder != "undefined" ? MozBlobBuilder : (typeof WebKitBlobBuilder != "undefined" ? WebKitBlobBuilder : (!Browser.hasBlobConstructor ? console.log("warning: no BlobBuilder") : null));
        Browser.URLObject = typeof window != "undefined" ? (window.URL ? window.URL : window.webkitURL) : undefined;
        if (!Module.noImageDecoding && typeof Browser.URLObject === 'undefined') {
            console.log("warning: Browser does not support creating object URLs. Built-in browser image decoding will not be available.");
            Module.noImageDecoding = true;
        }

        // Support for plugins that can process preloaded files. You can add more of these to
        // your app by creating and appending to Module.preloadPlugins.
        //
        // Each plugin is asked if it can handle a file based on the file's name. If it can,
        // it is given the file's raw data. When it is done, it calls a callback with the file's
        // (possibly modified) data. For example, a plugin might decompress a file, or it
        // might create some side data structure for use later (like an Image element, etc.).

        var imagePlugin = {};
        imagePlugin['canHandle'] = function imagePlugin_canHandle(name) {
            return !Module.noImageDecoding && /\.(jpg|jpeg|png|bmp)$/i.test(name);
        };
        imagePlugin['handle'] = function imagePlugin_handle(byteArray, name, onload, onerror) {
            var b = null;
            if (Browser.hasBlobConstructor) {
                try {
                    b = new Blob([byteArray], {
                        type: Browser.getMimetype(name)
                    });
                    if (b.size !== byteArray.length) { // Safari bug #118630
                        // Safari's Blob can only take an ArrayBuffer
                        b = new Blob([(new Uint8Array(byteArray)).buffer], {
                            type: Browser.getMimetype(name)
                        });
                    }
                } catch (e) {
                    Runtime.warnOnce('Blob constructor present but fails: ' + e + '; falling back to blob builder');
                }
            }
            if (!b) {
                var bb = new Browser.BlobBuilder();
                bb.append((new Uint8Array(byteArray)).buffer); // we need to pass a buffer, and must copy the array to get the right data range
                b = bb.getBlob();
            }
            var url = Browser.URLObject.createObjectURL(b);
            var img = new Image();
            img.onload = function img_onload() {
                assert(img.complete, 'Image ' + name + ' could not be decoded');
                var canvas = document.createElement('canvas');
                canvas.width = img.width;
                canvas.height = img.height;
                var ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0);
                Module["preloadedImages"][name] = canvas;
                Browser.URLObject.revokeObjectURL(url);
                if (onload) onload(byteArray);
            };
            img.onerror = function img_onerror(event) {
                console.log('Image ' + url + ' could not be decoded');
                if (onerror) onerror();
            };
            img.src = url;
        };
        Module['preloadPlugins'].push(imagePlugin);

        var audioPlugin = {};
        audioPlugin['canHandle'] = function audioPlugin_canHandle(name) {
            return !Module.noAudioDecoding && name.substr(-4) in {
                '.ogg': 1,
                '.wav': 1,
                '.mp3': 1
            };
        };
        audioPlugin['handle'] = function audioPlugin_handle(byteArray, name, onload, onerror) {
            var done = false;

            function finish(audio) {
                if (done) return;
                done = true;
                Module["preloadedAudios"][name] = audio;
                if (onload) onload(byteArray);
            }

            function fail() {
                if (done) return;
                done = true;
                Module["preloadedAudios"][name] = new Audio(); // empty shim
                if (onerror) onerror();
            }
            if (Browser.hasBlobConstructor) {
                try {
                    var b = new Blob([byteArray], {
                        type: Browser.getMimetype(name)
                    });
                } catch (e) {
                    return fail();
                }
                var url = Browser.URLObject.createObjectURL(b); // XXX we never revoke this!
                var audio = new Audio();
                audio.addEventListener('canplaythrough', function() {
                    finish(audio)
                }, false); // use addEventListener due to chromium bug 124926
                audio.onerror = function audio_onerror(event) {
                    if (done) return;
                    console.log('warning: browser could not fully decode audio ' + name + ', trying slower base64 approach');

                    function encode64(data) {
                        var BASE = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
                        var PAD = '=';
                        var ret = '';
                        var leftchar = 0;
                        var leftbits = 0;
                        for (var i = 0; i < data.length; i++) {
                            leftchar = (leftchar << 8) | data[i];
                            leftbits += 8;
                            while (leftbits >= 6) {
                                var curr = (leftchar >> (leftbits - 6)) & 0x3f;
                                leftbits -= 6;
                                ret += BASE[curr];
                            }
                        }
                        if (leftbits == 2) {
                            ret += BASE[(leftchar & 3) << 4];
                            ret += PAD + PAD;
                        } else if (leftbits == 4) {
                            ret += BASE[(leftchar & 0xf) << 2];
                            ret += PAD;
                        }
                        return ret;
                    }
                    audio.src = 'data:audio/x-' + name.substr(-3) + ';base64,' + encode64(byteArray);
                    finish(audio); // we don't wait for confirmation this worked - but it's worth trying
                };
                audio.src = url;
                // workaround for chrome bug 124926 - we do not always get oncanplaythrough or onerror
                Browser.safeSetTimeout(function() {
                    finish(audio); // try to use it even though it is not necessarily ready to play
                }, 10000);
            } else {
                return fail();
            }
        };
        Module['preloadPlugins'].push(audioPlugin);

        // Canvas event setup

        var canvas = Module['canvas'];
        canvas.requestPointerLock = canvas['requestPointerLock'] ||
            canvas['mozRequestPointerLock'] ||
            canvas['webkitRequestPointerLock'];
        canvas.exitPointerLock = document['exitPointerLock'] ||
            document['mozExitPointerLock'] ||
            document['webkitExitPointerLock'] ||
            function() {}; // no-op if function does not exist
        canvas.exitPointerLock = canvas.exitPointerLock.bind(document);

        function pointerLockChange() {
            Browser.pointerLock = document['pointerLockElement'] === canvas ||
                document['mozPointerLockElement'] === canvas ||
                document['webkitPointerLockElement'] === canvas;
        }

        document.addEventListener('pointerlockchange', pointerLockChange, false);
        document.addEventListener('mozpointerlockchange', pointerLockChange, false);
        document.addEventListener('webkitpointerlockchange', pointerLockChange, false);

        if (Module['elementPointerLock']) {
            canvas.addEventListener("click", function(ev) {
                if (!Browser.pointerLock && canvas.requestPointerLock) {
                    canvas.requestPointerLock();
                    ev.preventDefault();
                }
            }, false);
        }
    },
    createContext: function(canvas, useWebGL, setInModule, webGLContextAttributes) {
        var ctx;
        try {
            if (useWebGL) {
                var contextAttributes = {
                    antialias: false,
                    alpha: false
                };

                if (webGLContextAttributes) {
                    for (var attribute in webGLContextAttributes) {
                        contextAttributes[attribute] = webGLContextAttributes[attribute];
                    }
                }


                var errorInfo = '?';

                function onContextCreationError(event) {
                    errorInfo = event.statusMessage || errorInfo;
                }
                canvas.addEventListener('webglcontextcreationerror', onContextCreationError, false);
                try {
                    ['experimental-webgl', 'webgl'].some(function(webglId) {
                        return ctx = canvas.getContext(webglId, contextAttributes);
                    });
                } finally {
                    canvas.removeEventListener('webglcontextcreationerror', onContextCreationError, false);
                }
            } else {
                ctx = canvas.getContext('2d');
            }
            if (!ctx) throw ':(';
        } catch (e) {
            Module.print('Could not create canvas: ' + [errorInfo, e]);
            return null;
        }
        if (useWebGL) {
            // Set the background of the WebGL canvas to black
            canvas.style.backgroundColor = "black";

            // Warn on context loss
            canvas.addEventListener('webglcontextlost', function(event) {
                alert('WebGL context lost. You will need to reload the page.');
            }, false);
        }
        if (setInModule) {
            GLctx = Module.ctx = ctx;
            Module.useWebGL = useWebGL;
            Browser.moduleContextCreatedCallbacks.forEach(function(callback) {
                callback()
            });
            Browser.init();
        }
        return ctx;
    },
    destroyContext: function(canvas, useWebGL, setInModule) {},
    fullScreenHandlersInstalled: false,
    lockPointer: undefined,
    resizeCanvas: undefined,
    requestFullScreen: function(lockPointer, resizeCanvas) {
        Browser.lockPointer = lockPointer;
        Browser.resizeCanvas = resizeCanvas;
        if (typeof Browser.lockPointer === 'undefined') Browser.lockPointer = true;
        if (typeof Browser.resizeCanvas === 'undefined') Browser.resizeCanvas = false;

        var canvas = Module['canvas'];

        function fullScreenChange() {
            Browser.isFullScreen = false;
            if ((document['webkitFullScreenElement'] || document['webkitFullscreenElement'] ||
                    document['mozFullScreenElement'] || document['mozFullscreenElement'] ||
                    document['fullScreenElement'] || document['fullscreenElement']) === canvas) {
                canvas.cancelFullScreen = document['cancelFullScreen'] ||
                    document['mozCancelFullScreen'] ||
                    document['webkitCancelFullScreen'];
                canvas.cancelFullScreen = canvas.cancelFullScreen.bind(document);
                if (Browser.lockPointer) canvas.requestPointerLock();
                Browser.isFullScreen = true;
                if (Browser.resizeCanvas) Browser.setFullScreenCanvasSize();
            } else if (Browser.resizeCanvas) {
                Browser.setWindowedCanvasSize();
            }
            if (Module['onFullScreen']) Module['onFullScreen'](Browser.isFullScreen);
        }

        if (!Browser.fullScreenHandlersInstalled) {
            Browser.fullScreenHandlersInstalled = true;
            document.addEventListener('fullscreenchange', fullScreenChange, false);
            document.addEventListener('mozfullscreenchange', fullScreenChange, false);
            document.addEventListener('webkitfullscreenchange', fullScreenChange, false);
        }

        canvas.requestFullScreen = canvas['requestFullScreen'] ||
            canvas['mozRequestFullScreen'] ||
            (canvas['webkitRequestFullScreen'] ? function() {
                canvas['webkitRequestFullScreen'](Element['ALLOW_KEYBOARD_INPUT'])
            } : null);
        canvas.requestFullScreen();
    },
    requestAnimationFrame: function requestAnimationFrame(func) {
        if (typeof window === 'undefined') { // Provide fallback to setTimeout if window is undefined (e.g. in Node.js)
            setTimeout(func, 1000 / 60);
        } else {
            if (!window.requestAnimationFrame) {
                window.requestAnimationFrame = window['requestAnimationFrame'] ||
                    window['mozRequestAnimationFrame'] ||
                    window['webkitRequestAnimationFrame'] ||
                    window['msRequestAnimationFrame'] ||
                    window['oRequestAnimationFrame'] ||
                    window['setTimeout'];
            }
            window.requestAnimationFrame(func);
        }
    },
    safeCallback: function(func) {
        return function() {
            if (!ABORT) return func.apply(null, arguments);
        };
    },
    safeRequestAnimationFrame: function(func) {
        return Browser.requestAnimationFrame(function() {
            if (!ABORT) func();
        });
    },
    safeSetTimeout: function(func, timeout) {
        return setTimeout(function() {
            if (!ABORT) func();
        }, timeout);
    },
    safeSetInterval: function(func, timeout) {
        return setInterval(function() {
            if (!ABORT) func();
        }, timeout);
    },
    getMimetype: function(name) {
        return {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'bmp': 'image/bmp',
            'ogg': 'audio/ogg',
            'wav': 'audio/wav',
            'mp3': 'audio/mpeg'
        }[name.substr(name.lastIndexOf('.') + 1)];
    },
    getUserMedia: function(func) {
        if (!window.getUserMedia) {
            window.getUserMedia = navigator['getUserMedia'] ||
                navigator['mozGetUserMedia'];
        }
        window.getUserMedia(func);
    },
    getMovementX: function(event) {
        return event['movementX'] ||
            event['mozMovementX'] ||
            event['webkitMovementX'] ||
            0;
    },
    getMovementY: function(event) {
        return event['movementY'] ||
            event['mozMovementY'] ||
            event['webkitMovementY'] ||
            0;
    },
    mouseX: 0,
    mouseY: 0,
    mouseMovementX: 0,
    mouseMovementY: 0,
    calculateMouseEvent: function(event) { // event should be mousemove, mousedown or mouseup
        if (Browser.pointerLock) {
            // When the pointer is locked, calculate the coordinates
            // based on the movement of the mouse.
            // Workaround for Firefox bug 764498
            if (event.type != 'mousemove' &&
                ('mozMovementX' in event)) {
                Browser.mouseMovementX = Browser.mouseMovementY = 0;
            } else {
                Browser.mouseMovementX = Browser.getMovementX(event);
                Browser.mouseMovementY = Browser.getMovementY(event);
            }

            // check if SDL is available
            if (typeof SDL != "undefined") {
                Browser.mouseX = SDL.mouseX + Browser.mouseMovementX;
                Browser.mouseY = SDL.mouseY + Browser.mouseMovementY;
            } else {
                // just add the mouse delta to the current absolut mouse position
                // FIXME: ideally this should be clamped against the canvas size and zero
                Browser.mouseX += Browser.mouseMovementX;
                Browser.mouseY += Browser.mouseMovementY;
            }
        } else {
            // Otherwise, calculate the movement based on the changes
            // in the coordinates.
            var rect = Module["canvas"].getBoundingClientRect();
            var x, y;

            // Neither .scrollX or .pageXOffset are defined in a spec, but
            // we prefer .scrollX because it is currently in a spec draft.
            // (see: http://www.w3.org/TR/2013/WD-cssom-view-20131217/)
            var scrollX = ((typeof window.scrollX !== 'undefined') ? window.scrollX : window.pageXOffset);
            var scrollY = ((typeof window.scrollY !== 'undefined') ? window.scrollY : window.pageYOffset);
            if (event.type == 'touchstart' ||
                event.type == 'touchend' ||
                event.type == 'touchmove') {
                var t = event.touches.item(0);
                if (t) {
                    x = t.pageX - (scrollX + rect.left);
                    y = t.pageY - (scrollY + rect.top);
                } else {
                    return;
                }
            } else {
                x = event.pageX - (scrollX + rect.left);
                y = event.pageY - (scrollY + rect.top);
            }

            // the canvas might be CSS-scaled compared to its backbuffer;
            // SDL-using content will want mouse coordinates in terms
            // of backbuffer units.
            var cw = Module["canvas"].width;
            var ch = Module["canvas"].height;
            x = x * (cw / rect.width);
            y = y * (ch / rect.height);

            Browser.mouseMovementX = x - Browser.mouseX;
            Browser.mouseMovementY = y - Browser.mouseY;
            Browser.mouseX = x;
            Browser.mouseY = y;
        }
    },
    xhrLoad: function(url, onload, onerror) {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', url, true);
        xhr.responseType = 'arraybuffer';
        xhr.onload = function xhr_onload() {
            if (xhr.status == 200 || (xhr.status == 0 && xhr.response)) { // file URLs can return 0
                onload(xhr.response);
            } else {
                onerror();
            }
        };
        xhr.onerror = onerror;
        xhr.send(null);
    },
    asyncLoad: function(url, onload, onerror, noRunDep) {
        Browser.xhrLoad(url, function(arrayBuffer) {
            assert(arrayBuffer, 'Loading data file "' + url + '" failed (no arrayBuffer).');
            onload(new Uint8Array(arrayBuffer));
            if (!noRunDep) removeRunDependency('al ' + url);
        }, function(event) {
            if (onerror) {
                onerror();
            } else {
                throw 'Loading data file "' + url + '" failed.';
            }
        });
        if (!noRunDep) addRunDependency('al ' + url);
    },
    resizeListeners: [],
    updateResizeListeners: function() {
        var canvas = Module['canvas'];
        Browser.resizeListeners.forEach(function(listener) {
            listener(canvas.width, canvas.height);
        });
    },
    setCanvasSize: function(width, height, noUpdates) {
        var canvas = Module['canvas'];
        canvas.width = width;
        canvas.height = height;
        if (!noUpdates) Browser.updateResizeListeners();
    },
    windowedWidth: 0,
    windowedHeight: 0,
    setFullScreenCanvasSize: function() {
        var canvas = Module['canvas'];
        this.windowedWidth = canvas.width;
        this.windowedHeight = canvas.height;
        canvas.width = screen.width;
        canvas.height = screen.height;
        // check if SDL is available   
        if (typeof SDL != "undefined") {
            var flags = HEAPU32[((SDL.screen + Runtime.QUANTUM_SIZE * 0) >> 2)];
            flags = flags | 0x00800000; // set SDL_FULLSCREEN flag
            HEAP32[((SDL.screen + Runtime.QUANTUM_SIZE * 0) >> 2)] = flags
        }
        Browser.updateResizeListeners();
    },
    setWindowedCanvasSize: function() {
        var canvas = Module['canvas'];
        canvas.width = this.windowedWidth;
        canvas.height = this.windowedHeight;
        // check if SDL is available       
        if (typeof SDL != "undefined") {
            var flags = HEAPU32[((SDL.screen + Runtime.QUANTUM_SIZE * 0) >> 2)];
            flags = flags & ~0x00800000; // clear SDL_FULLSCREEN flag
            HEAP32[((SDL.screen + Runtime.QUANTUM_SIZE * 0) >> 2)] = flags
        }
        Browser.updateResizeListeners();
    }
};
FS.staticInit();
__ATINIT__.unshift({
    func: function() {
        if (!Module["noFSInit"] && !FS.init.initialized) FS.init()
    }
});
__ATMAIN__.push({
    func: function() {
        FS.ignorePermissions = false
    }
});
__ATEXIT__.push({
    func: function() {
        FS.quit()
    }
});
Module["FS_createFolder"] = FS.createFolder;
Module["FS_createPath"] = FS.createPath;
Module["FS_createDataFile"] = FS.createDataFile;
Module["FS_createPreloadedFile"] = FS.createPreloadedFile;
Module["FS_createLazyFile"] = FS.createLazyFile;
Module["FS_createLink"] = FS.createLink;
Module["FS_createDevice"] = FS.createDevice;
___errno_state = Runtime.staticAlloc(4);
HEAP32[((___errno_state) >> 2)] = 0;
__ATINIT__.unshift({
    func: function() {
        TTY.init()
    }
});
__ATEXIT__.push({
    func: function() {
        TTY.shutdown()
    }
});
TTY.utf8 = new Runtime.UTF8Processor();
if (ENVIRONMENT_IS_NODE) {
    var fs = require("fs");
    NODEFS.staticInit();
}
__ATINIT__.push({
    func: function() {
        SOCKFS.root = FS.mount(SOCKFS, {}, null);
    }
});
_fputc.ret = allocate([0], "i8", ALLOC_STATIC);
Module["requestFullScreen"] = function Module_requestFullScreen(lockPointer, resizeCanvas) {
    Browser.requestFullScreen(lockPointer, resizeCanvas)
};
Module["requestAnimationFrame"] = function Module_requestAnimationFrame(func) {
    Browser.requestAnimationFrame(func)
};
Module["setCanvasSize"] = function Module_setCanvasSize(width, height, noUpdates) {
    Browser.setCanvasSize(width, height, noUpdates)
};
Module["pauseMainLoop"] = function Module_pauseMainLoop() {
    Browser.mainLoop.pause()
};
Module["resumeMainLoop"] = function Module_resumeMainLoop() {
    Browser.mainLoop.resume()
};
Module["getUserMedia"] = function Module_getUserMedia() {
    Browser.getUserMedia()
}
STACK_BASE = STACKTOP = Runtime.alignMemory(STATICTOP);

staticSealed = true; // seal the static portion of memory

STACK_MAX = STACK_BASE + 5242880;

DYNAMIC_BASE = DYNAMICTOP = Runtime.alignMemory(STACK_MAX);

assert(DYNAMIC_BASE < TOTAL_MEMORY, "TOTAL_MEMORY not big enough for stack");


var Math_min = Math.min;

function invoke_vi(index, a1) {
    try {
        Module["dynCall_vi"](index, a1);
    } catch (e) {
        if (typeof e !== 'number' && e !== 'longjmp') throw e;
        asm["setThrew"](1, 0);
    }
}

function invoke_vii(index, a1, a2) {
    try {
        Module["dynCall_vii"](index, a1, a2);
    } catch (e) {
        if (typeof e !== 'number' && e !== 'longjmp') throw e;
        asm["setThrew"](1, 0);
    }
}

function invoke_ii(index, a1) {
    try {
        return Module["dynCall_ii"](index, a1);
    } catch (e) {
        if (typeof e !== 'number' && e !== 'longjmp') throw e;
        asm["setThrew"](1, 0);
    }
}

function invoke_ff(index, a1) {
    try {
        return Module["dynCall_ff"](index, a1);
    } catch (e) {
        if (typeof e !== 'number' && e !== 'longjmp') throw e;
        asm["setThrew"](1, 0);
    }
}

function invoke_v(index) {
    try {
        Module["dynCall_v"](index);
    } catch (e) {
        if (typeof e !== 'number' && e !== 'longjmp') throw e;
        asm["setThrew"](1, 0);
    }
}

function invoke_iii(index, a1, a2) {
    try {
        return Module["dynCall_iii"](index, a1, a2);
    } catch (e) {
        if (typeof e !== 'number' && e !== 'longjmp') throw e;
        asm["setThrew"](1, 0);
    }
}

function asmPrintInt(x, y) {
    Module.print('int ' + x + ',' + y); // + ' ' + new Error().stack);
}

function asmPrintFloat(x, y) {
        Module.print('float ' + x + ',' + y); // + ' ' + new Error().stack);
    }
    // EMSCRIPTEN_START_ASM
var asm = (function(global, env, buffer) {
    "use asm";
    var a = new global.Int8Array(buffer);
    var b = new global.Int16Array(buffer);
    var c = new global.Int32Array(buffer);
    var d = new global.Uint8Array(buffer);
    var e = new global.Uint16Array(buffer);
    var f = new global.Uint32Array(buffer);
    var g = new global.Float32Array(buffer);
    var h = new global.Float64Array(buffer);
    var i = env.STACKTOP | 0;
    var j = env.STACK_MAX | 0;
    var k = env.tempDoublePtr | 0;
    var l = env.ABORT | 0;
    var m = +env.NaN;
    var n = +env.Infinity;
    var o = 0;
    var p = 0;
    var q = 0;
    var r = 0;
    var s = 0,
        t = 0,
        u = 0,
        v = 0,
        w = 0.0,
        x = 0,
        y = 0,
        z = 0,
        A = 0.0;
    var B = 0;
    var C = 0;
    var D = 0;
    var E = 0;
    var F = 0;
    var G = 0;
    var H = 0;
    var I = 0;
    var J = 0;
    var K = 0;
    var L = global.Math.floor;
    var M = global.Math.abs;
    var N = global.Math.sqrt;
    var O = global.Math.pow;
    var P = global.Math.cos;
    var Q = global.Math.sin;
    var R = global.Math.tan;
    var S = global.Math.acos;
    var T = global.Math.asin;
    var U = global.Math.atan;
    var V = global.Math.atan2;
    var W = global.Math.exp;
    var X = global.Math.log;
    var Y = global.Math.ceil;
    var Z = global.Math.imul;
    var _ = env.abort;
    var $ = env.assert;
    var aa = env.asmPrintInt;
    var ba = env.asmPrintFloat;
    var ca = env.min;
    var da = env.invoke_vi;
    var ea = env.invoke_vii;
    var fa = env.invoke_ii;
    var ga = env.invoke_ff;
    var ha = env.invoke_v;
    var ia = env.invoke_iii;
    var ja = env._strncmp;
    var ka = env._fabsf;
    var la = env._sysconf;
    var ma = env._abort;
    var na = env._fprintf;
    var oa = env._printf;
    var pa = env._fflush;
    var qa = env.__reallyNegative;
    var ra = env._sqrtf;
    var sa = env._fputc;
    var ta = env._fabs;
    var ua = env.___setErrNo;
    var va = env._fwrite;
    var wa = env._send;
    var xa = env._write;
    var ya = env._fputs;
    var za = env._log10;
    var Aa = env._sin;
    var Ba = env._ceilf;
    var Ca = env.__formatString;
    var Da = env._cos;
    var Ea = env._pwrite;
    var Fa = env._puts;
    var Ga = env._sbrk;
    var Ha = env.___errno_location;
    var Ia = env._atan2;
    var Ja = env._time;
    var Ka = env._strcmp;
    var La = 0.0;
    // EMSCRIPTEN_START_FUNCS
    function Sa(a) {
        a = a | 0;
        var b = 0;
        b = i;
        i = i + a | 0;
        i = i + 7 & -8;
        return b | 0
    }

    function Ta() {
        return i | 0
    }

    function Ua(a) {
        a = a | 0;
        i = a
    }

    function Va(a, b) {
        a = a | 0;
        b = b | 0;
        if ((o | 0) == 0) {
            o = a;
            p = b
        }
    }

    function Wa(b) {
        b = b | 0;
        a[k] = a[b];
        a[k + 1 | 0] = a[b + 1 | 0];
        a[k + 2 | 0] = a[b + 2 | 0];
        a[k + 3 | 0] = a[b + 3 | 0]
    }

    function Xa(b) {
        b = b | 0;
        a[k] = a[b];
        a[k + 1 | 0] = a[b + 1 | 0];
        a[k + 2 | 0] = a[b + 2 | 0];
        a[k + 3 | 0] = a[b + 3 | 0];
        a[k + 4 | 0] = a[b + 4 | 0];
        a[k + 5 | 0] = a[b + 5 | 0];
        a[k + 6 | 0] = a[b + 6 | 0];
        a[k + 7 | 0] = a[b + 7 | 0]
    }

    function Ya(a) {
        a = a | 0;
        B = a
    }

    function Za(a) {
        a = a | 0;
        C = a
    }

    function _a(a) {
        a = a | 0;
        D = a
    }

    function $a(a) {
        a = a | 0;
        E = a
    }

    function ab(a) {
        a = a | 0;
        F = a
    }

    function bb(a) {
        a = a | 0;
        G = a
    }

    function cb(a) {
        a = a | 0;
        H = a
    }

    function db(a) {
        a = a | 0;
        I = a
    }

    function eb(a) {
        a = a | 0;
        J = a
    }

    function fb(a) {
        a = a | 0;
        K = a
    }

    function gb() {}

    function hb(a) {
        a = a | 0;
        ac(c[a + 12 >> 2] | 0);
        return
    }

    function ib(a) {
        a = a | 0;
        if ((Ka(2160, a | 0) | 0) == 0) {
            return 0
        } else {
            a = (Ka(2144, a | 0) | 0) == 0;
            return (a ? 1 : 2) | 0
        }
        return 0
    }

    function jb(a) {
        a = a | 0;
        if ((a | 0) == 1) {
            a = 2144
        } else if ((a | 0) == 2) {
            a = 2136
        } else if ((a | 0) == 0) {
            a = 2160
        } else {
            a = 2128
        }
        return a | 0
    }

    function kb(a) {
        a = +a;
        a = a * .5 + .5;
        return +(.42 - +P(a * 6.2831854820251465) * .5 + +P(a * 12.566370964050293) * .08)
    }

    function lb(a) {
        a = +a;
        return +(.54 - +P((a * .5 + .5) * 6.2831854820251465) * .46)
    }

    function mb(a) {
        a = +a;
        return +1.0
    }

    function nb(a, b, c, d) {
        a = a | 0;
        b = b | 0;
        c = +c;
        d = d | 0;
        var e = 0,
            f = 0.0,
            h = 0,
            i = 0.0,
            j = 0.0;
        e = (b | 0) / 2 | 0;
        if ((d | 0) == 1) {
            d = 6
        } else if ((d | 0) == 0) {
            d = 2
        } else {
            d = 4
        }
        c = c * 6.2831854820251465;
        g[a + (e << 2) >> 2] = c * +Pa[d & 7](0.0);
        if ((b | 0) >= 2) {
            f = +(e | 0);
            h = 1;
            do {
                i = +(h | 0);
                j = +Q(c * i) / +(h | 0);
                i = j * +Pa[d & 7](i / f);
                g[a + (h + e << 2) >> 2] = i;
                g[a + (e - h << 2) >> 2] = i;
                h = h + 1 | 0;
            } while ((e | 0) >= (h | 0))
        }
        e = (b | 0) > 0;
        if (e) {
            c = 0.0;
            d = 0
        } else {
            return
        }
        do {
            c = c + +g[a + (d << 2) >> 2];
            d = d + 1 | 0;
        } while ((d | 0) < (b | 0));
        if (e) {
            e = 0
        } else {
            return
        }
        do {
            h = a + (e << 2) | 0;
            g[h >> 2] = +g[h >> 2] / c;
            e = e + 1 | 0;
        } while ((e | 0) < (b | 0));
        return
    }

    function ob(a, b, c, d, e) {
        a = a | 0;
        b = b | 0;
        c = +c;
        d = +d;
        e = e | 0;
        var f = 0,
            h = 0,
            i = 0.0,
            j = 0.0,
            k = 0,
            l = 0.0,
            m = 0.0;
        f = bc(b << 2) | 0;
        i = (d - c) * .5;
        h = (b | 0) / 2 | 0;
        if ((e | 0) == 0) {
            e = 2
        } else if ((e | 0) == 1) {
            e = 6
        } else {
            e = 4
        }
        j = i * 6.2831854820251465;
        g[f + (h << 2) >> 2] = j * +Pa[e & 7](0.0);
        if ((b | 0) >= 2) {
            i = +(h | 0);
            k = 1;
            do {
                l = +(k | 0);
                m = +Q(j * l) / +(k | 0);
                l = m * +Pa[e & 7](l / i);
                g[f + (k + h << 2) >> 2] = l;
                g[f + (h - k << 2) >> 2] = l;
                k = k + 1 | 0;
            } while ((h | 0) >= (k | 0))
        }
        h = (b | 0) > 0;
        if (h) {
            i = 0.0;
            e = 0
        } else {
            return
        }
        while (1) {
            i = i + +g[f + (e << 2) >> 2];
            e = e + 1 | 0;
            if ((e | 0) >= (b | 0)) {
                e = 0;
                break
            }
        }
        do {
            k = f + (e << 2) | 0;
            g[k >> 2] = +g[k >> 2] / i;
            e = e + 1 | 0;
        } while ((e | 0) < (b | 0));
        if (!h) {
            return
        }
        c = (c + d) * .5 * 6.2831854820251465;
        j = 0.0;
        h = 0;
        do {
            d = j;
            i = +P(d);
            d = +Q(d);
            j = c + j;
            if (j > 6.2831854820251465) {
                do {
                    j = j + -6.2831854820251465;
                } while (j > 6.2831854820251465)
            }
            if (j < 0.0) {
                do {
                    j = j + 6.2831854820251465;
                } while (j < 0.0)
            }
            m = +g[f + (h << 2) >> 2];
            k = a + (h << 3) | 0;
            g[k >> 2] = i * m;
            g[k + 4 >> 2] = d * m;
            h = h + 1 | 0;
        } while ((h | 0) < (b | 0));
        return
    }

    function pb(a) {
        a = +a;
        var b = 0;
        b = ~~(4.0 / a);
        return (b & 1 ^ 1) + b | 0
    }

    function qb(a, b, c, d, e) {
        a = a | 0;
        b = b | 0;
        c = c | 0;
        d = +d;
        e = +e;
        var f = 0,
            h = 0,
            i = 0,
            j = 0.0,
            k = 0,
            l = 0.0;
        d = d * 2.0 * 3.1415927410125732;
        if ((c | 0) > 0) {
            f = 0
        } else {
            return +e
        }
        do {
            l = e;
            j = +P(l);
            l = +Q(l);
            k = a + (f << 3) | 0;
            i = k + 4 | 0;
            h = b + (f << 3) | 0;
            g[h >> 2] = j * +g[k >> 2] - l * +g[i >> 2];
            g[h + 4 >> 2] = l * +g[k >> 2] + j * +g[i >> 2];
            e = d + e;
            if (e > 6.2831854820251465) {
                do {
                    e = e + -6.2831854820251465;
                } while (e > 6.2831854820251465)
            }
            if (e < 0.0) {
                do {
                    e = e + 6.2831854820251465;
                } while (e < 0.0)
            }
            f = f + 1 | 0;
        } while ((f | 0) < (c | 0));
        return +e
    }

    function rb(a, b) {
        a = a | 0;
        b = b | 0;
        var d = 0,
            e = 0.0,
            f = 0;
        d = bc(b << 2) | 0;
        if ((b | 0) > 0) {
            e = +(b | 0);
            f = 0;
            do {
                g[d + (f << 2) >> 2] = +Q(+(f | 0) / e * 1.5707963705062866);
                f = f + 1 | 0;
            } while ((f | 0) < (b | 0))
        }
        c[a >> 2] = d;
        c[a + 4 >> 2] = b;
        return
    }

    function sb(a) {
        a = a | 0;
        var b = 0,
            d = 0;
        b = i;
        d = a;
        a = i;
        i = i + 8 | 0;
        c[a >> 2] = c[d >> 2];
        c[a + 4 >> 2] = c[d + 4 >> 2];
        cc(c[a >> 2] | 0);
        i = b;
        return
    }

    function tb(a, b, d, e, f, h) {
        a = a | 0;
        b = b | 0;
        d = d | 0;
        e = +e;
        f = f | 0;
        h = +h;
        var j = 0,
            k = 0.0,
            l = 0,
            m = 0,
            n = 0.0,
            o = 0,
            p = 0,
            q = 0,
            r = 0.0,
            s = 0;
        j = i;
        s = f;
        f = i;
        i = i + 8 | 0;
        c[f >> 2] = c[s >> 2];
        c[f + 4 >> 2] = c[s + 4 >> 2];
        e = e * 2.0 * 3.1415927410125732;
        if ((d | 0) <= 0) {
            r = h;
            i = j;
            return +r
        }
        l = c[f + 4 >> 2] | 0;
        k = +(l | 0);
        l = l - 1 | 0;
        f = c[f >> 2] | 0;
        m = 0;
        do {
            s = ~~(h / 1.5707963705062866);
            o = ~~((h - +(s | 0) * 1.5707963705062866) / 1.5707963705062866 * k);
            p = l - o | 0;
            q = (s & 1 | 0) == 0;
            if ((s | 0) == 0) {
                n = 1.0
            } else {
                n = (s | 0) < 3 ? -1.0 : 1.0
            }
            r = ((s | 0) > 1 ? -1.0 : 1.0) * +g[f + ((q ? o : p) << 2) >> 2];
            n = n * +g[f + ((q ? p : o) << 2) >> 2];
            p = a + (m << 3) | 0;
            q = p + 4 | 0;
            s = b + (m << 3) | 0;
            g[s >> 2] = n * +g[p >> 2] - r * +g[q >> 2];
            g[s + 4 >> 2] = r * +g[p >> 2] + n * +g[q >> 2];
            h = e + h;
            if (h > 6.2831854820251465) {
                do {
                    h = h + -6.2831854820251465;
                } while (h > 6.2831854820251465)
            }
            if (h < 0.0) {
                do {
                    h = h + 6.2831854820251465;
                } while (h < 0.0)
            }
            m = m + 1 | 0;
        } while ((m | 0) < (d | 0));
        i = j;
        return +h
    }

    function ub(a, b, c, d, e, f) {
        a = a | 0;
        b = b | 0;
        c = c | 0;
        d = d | 0;
        e = e | 0;
        f = f | 0;
        var h = 0,
            i = 0,
            j = 0.0,
            k = 0.0,
            l = 0;
        if ((c | 0) < 1 | (f | 0) > (c | 0)) {
            l = 0;
            return l | 0
        }
        if ((f | 0) > 0) {
            i = 0;
            h = 0
        } else {
            i = 0;
            a = 0;
            do {
                l = b + (i << 3) | 0;
                g[l >> 2] = 0.0;
                g[l + 4 >> 2] = 0.0;
                i = i + 1 | 0;
                a = a + d | 0;
            } while (!((a | 0) >= (c | 0) | (a + f | 0) > (c | 0)));
            return i | 0
        }
        do {
            j = 0.0;
            l = 0;
            while (1) {
                j = j + +g[a + (l + h << 3) >> 2] * +g[e + (l << 2) >> 2];
                l = l + 1 | 0;
                if ((l | 0) >= (f | 0)) {
                    k = 0.0;
                    l = 0;
                    break
                }
            }
            do {
                k = k + +g[a + (l + h << 3) + 4 >> 2] * +g[e + (l << 2) >> 2];
                l = l + 1 | 0;
            } while ((l | 0) < (f | 0));
            l = b + (i << 3) | 0;
            g[l >> 2] = j;
            g[l + 4 >> 2] = k;
            i = i + 1 | 0;
            h = h + d | 0;
        } while (!((h | 0) >= (c | 0) | (h + f | 0) > (c | 0)));
        return i | 0
    }

    function vb(a, b, d, e, f, h, i, j, k) {
        a = a | 0;
        b = b | 0;
        d = d | 0;
        e = e | 0;
        f = f | 0;
        h = h | 0;
        i = i | 0;
        j = j | 0;
        k = k | 0;
        var l = 0,
            m = 0,
            n = 0.0,
            o = 0,
            p = 0,
            q = 0,
            r = 0,
            s = 0,
            t = 0,
            u = 0.0;
        q = (Z(f, e) | 0) / (h | 0) | 0;
        a: do {
            if ((q | 0) > 0) {
                r = f - 1 - k | 0;
                p = (j | 0) / (f | 0) | 0;
                n = +(f | 0);
                l = 0;
                do {
                    m = Z(l, h) | 0;
                    o = (r + m | 0) / (f | 0) | 0;
                    m = (k - m + (Z(o, f) | 0) | 0) % (f | 0) | 0;
                    if ((p + o | 0) >= (e | 0)) {
                        break a
                    }
                    s = (j - m | 0) / (f | 0) | 0;
                    if ((s | 0) > 0) {
                        u = 0.0;
                        t = 0;
                        do {
                            u = u + +g[b + (t + o << 2) >> 2] * +g[i + ((Z(t, f) | 0) + m << 2) >> 2];
                            t = t + 1 | 0;
                        } while ((t | 0) < (s | 0))
                    } else {
                        u = 0.0
                    }
                    g[d + (l << 2) >> 2] = n * u;
                    l = l + 1 | 0;
                } while ((l | 0) < (q | 0))
            } else {
                o = 0;
                m = 0;
                l = 0
            }
        } while (0);
        c[a >> 2] = o;
        c[a + 4 >> 2] = l;
        c[a + 8 >> 2] = m;
        return
    }

    function wb(a, b, c, d, e) {
        a = a | 0;
        b = b | 0;
        c = c | 0;
        d = d | 0;
        e = e | 0;
        var f = 0.0,
            h = 0.0,
            i = 0.0,
            j = 0.0;
        f = 1.0 / +(c | 0);
        h = 1.0 / +(d | 0);
        f = (f < h ? f : h) * .5;
        d = (b | 0) / 2 | 0;
        if ((e | 0) == 1) {
            e = 6
        } else if ((e | 0) == 0) {
            e = 2
        } else {
            e = 4
        }
        h = f * 6.2831854820251465;
        g[a + (d << 2) >> 2] = h * +Pa[e & 7](0.0);
        if ((b | 0) >= 2) {
            f = +(d | 0);
            c = 1;
            do {
                i = +(c | 0);
                j = +Q(h * i) / +(c | 0);
                i = j * +Pa[e & 7](i / f);
                g[a + (c + d << 2) >> 2] = i;
                g[a + (d - c << 2) >> 2] = i;
                c = c + 1 | 0;
            } while ((d | 0) >= (c | 0))
        }
        if ((b | 0) > 0) {
            f = 0.0;
            d = 0
        } else {
            return
        }
        while (1) {
            f = f + +g[a + (d << 2) >> 2];
            d = d + 1 | 0;
            if ((d | 0) >= (b | 0)) {
                d = 0;
                break
            }
        }
        do {
            c = a + (d << 2) | 0;
            g[c >> 2] = +g[c >> 2] / f;
            d = d + 1 | 0;
        } while ((d | 0) < (b | 0));
        return
    }

    function xb(a, b, d, e, f, h, j, k) {
        a = a | 0;
        b = b | 0;
        d = d | 0;
        e = e | 0;
        f = +f;
        h = h | 0;
        j = j | 0;
        k = k | 0;
        var l = 0,
            m = 0,
            n = 0,
            o = 0,
            p = 0.0,
            q = 0,
            r = 0,
            s = 0,
            t = 0,
            u = 0,
            v = 0.0,
            w = 0,
            x = 0.0,
            y = 0.0;
        l = i;
        w = k;
        k = i;
        i = i + 12 | 0;
        i = i + 7 & -8;
        c[k >> 2] = c[w >> 2];
        c[k + 4 >> 2] = c[w + 4 >> 2];
        c[k + 8 >> 2] = c[w + 8 >> 2];
        if (f <= 1.0) {
            w = a;
            u = k;
            c[w >> 2] = c[u >> 2];
            c[w + 4 >> 2] = c[u + 4 >> 2];
            c[w + 8 >> 2] = c[u + 8 >> 2];
            i = l;
            return
        }
        m = k | 0;
        p = +g[m >> 2];
        if (p == 0.0) {
            if ((j | 0) > 0) {
                v = 0.0;
                o = 0;
                do {
                    v = v + +g[h + (o << 2) >> 2] * +g[b + (o << 2) >> 2];
                    o = o + 1 | 0;
                } while ((o | 0) < (j | 0))
            } else {
                v = 0.0
            }
            g[d >> 2] = v;
            q = 1;
            p = p + f
        } else {
            q = 0
        }
        r = ~~+Y(p);
        t = r - 1 | 0;
        if ((r + j | 0) < (e | 0)) {
            o = (j | 0) > 0;
            v = 0.0;
            s = -1;
            while (1) {
                do {
                    if ((s | 0) == (t | 0)) {
                        n = 12
                    } else {
                        s = r - 1 | 0;
                        if (o) {
                            v = 0.0;
                            n = 0
                        } else {
                            x = 0.0;
                            v = 0.0;
                            break
                        }
                        while (1) {
                            v = v + +g[h + (n << 2) >> 2] * +g[b + (s + n << 2) >> 2];
                            n = n + 1 | 0;
                            if ((n | 0) >= (j | 0)) {
                                n = 12;
                                break
                            }
                        }
                    }
                } while (0);
                do {
                    if ((n | 0) == 12) {
                        n = 0;
                        if (o) {
                            x = 0.0;
                            s = 0
                        } else {
                            x = 0.0;
                            break
                        }
                        do {
                            x = x + +g[h + (s << 2) >> 2] * +g[b + (s + r << 2) >> 2];
                            s = s + 1 | 0;
                        } while ((s | 0) < (j | 0))
                    }
                } while (0);
                y = p - +(r | 0) + 1.0;
                u = q + 1 | 0;
                g[d + (q << 2) >> 2] = (1.0 - y) * v + y * x;
                p = p + f;
                w = ~~+Y(p);
                t = w - 1 | 0;
                if ((w + j | 0) < (e | 0)) {
                    v = x;
                    s = r;
                    q = u;
                    r = w
                } else {
                    q = u;
                    break
                }
            }
        }
        c[k + 4 >> 2] = t;
        g[m >> 2] = p - +(t | 0);
        c[k + 8 >> 2] = q;
        w = a;
        u = k;
        c[w >> 2] = c[u >> 2];
        c[w + 4 >> 2] = c[u + 4 >> 2];
        c[w + 8 >> 2] = c[u + 8 >> 2];
        i = l;
        return
    }

    function yb(a, b, d, e, f) {
        a = a | 0;
        b = b | 0;
        d = d | 0;
        e = e | 0;
        f = f | 0;
        var h = 0,
            i = 0,
            j = 0,
            k = 0,
            l = 0,
            m = 0,
            n = 0,
            o = 0,
            p = 0;
        hb(a);
        h = a | 0;
        if ((c[h >> 2] | 0) > 0) {
            a = c[a + 8 >> 2] | 0;
            i = c[b + 4 >> 2] | 0;
            j = 0;
            do {
                p = j << 1;
                o = a + (p << 2) | 0;
                l = d + (j << 3) | 0;
                k = p | 1;
                m = a + (k << 2) | 0;
                n = l + 4 | 0;
                g[i + (p << 2) >> 2] = +g[o >> 2] * +g[l >> 2] - +g[m >> 2] * +g[n >> 2];
                g[i + (k << 2) >> 2] = +g[o >> 2] * +g[n >> 2] + +g[m >> 2] * +g[l >> 2];
                j = j + 1 | 0;
            } while ((j | 0) < (c[h >> 2] | 0))
        }
        hb(b);
        d = c[b + 8 >> 2] | 0;
        i = c[h >> 2] | 0;
        if ((i | 0) > 0) {
            a = d;
            b = 0;
            do {
                p = b << 1;
                o = a + (p << 2) | 0;
                g[o >> 2] = +g[o >> 2] / +(i | 0);
                p = a + ((p | 1) << 2) | 0;
                g[p >> 2] = +g[p >> 2] / +(c[h >> 2] | 0);
                b = b + 1 | 0;
                i = c[h >> 2] | 0;
            } while ((b | 0) < (i | 0))
        }
        if ((f | 0) <= 0) {
            return
        }
        h = 0;
        do {
            p = h << 1;
            n = d + (p << 2) | 0;
            o = e + (h << 3) | 0;
            g[n >> 2] = +g[n >> 2] + +g[o >> 2];
            p = d + ((p | 1) << 2) | 0;
            g[p >> 2] = +g[p >> 2] + +g[o + 4 >> 2];
            h = h + 1 | 0;
        } while ((h | 0) < (f | 0));
        return
    }

    function zb(a, b, c) {
        a = a | 0;
        b = b | 0;
        c = c | 0;
        var d = 0,
            e = 0,
            f = 0.0,
            h = 0.0,
            i = 0;
        d = (c | 0) > 0;
        if (d) {
            e = 0
        } else {
            return
        }
        do {
            i = a + (e << 3) | 0;
            h = +g[i >> 2];
            f = +g[i + 4 >> 2];
            g[b + (e << 2) >> 2] = h * h + f * f;
            e = e + 1 | 0;
        } while ((e | 0) < (c | 0));
        if (d) {
            a = 0
        } else {
            return
        }
        do {
            i = b + (a << 2) | 0;
            g[i >> 2] = +N(+g[i >> 2]);
            a = a + 1 | 0;
        } while ((a | 0) < (c | 0));
        return
    }

    function Ab(a, b, c, d, e) {
        a = a | 0;
        b = b | 0;
        c = c | 0;
        d = +d;
        e = +e;
        var f = 0,
            h = 0.0,
            i = 0,
            j = 0.0;
        f = d == 0.0;
        d = f ? .9475436210632324 : d;
        e = f ? .39248543977737427 : e;
        if ((c | 0) > 0) {
            f = 0
        } else {
            return
        }
        do {
            i = a + (f << 3) | 0;
            h = +g[i >> 2];
            if (h < 0.0) {
                h = -0.0 - h
            }
            j = +g[i + 4 >> 2];
            if (j < 0.0) {
                j = -0.0 - j
            }
            g[b + (f << 2) >> 2] = d * (j > h ? j : h) + e * (j < h ? j : h);
            f = f + 1 | 0;
        } while ((f | 0) < (c | 0));
        return
    }

    function Bb(a, b, d, e, f, h) {
        a = a | 0;
        b = b | 0;
        d = d | 0;
        e = e | 0;
        f = +f;
        h = h | 0;
        var j = 0,
            k = 0,
            l = 0,
            m = 0,
            n = 0.0;
        j = i;
        m = h;
        h = i;
        i = i + 8 | 0;
        c[h >> 2] = c[m >> 2];
        c[h + 4 >> 2] = c[m + 4 >> 2];
        f = f == 0.0 ? .9990000128746033 : f;
        k = h | 0;
        l = h + 4 | 0;
        n = +g[b >> 2] - +g[k >> 2] + f * +g[l >> 2];
        g[d >> 2] = n;
        if ((e | 0) > 1) {
            m = 1;
            do {
                n = +g[b + (m << 2) >> 2] - +g[b + (m - 1 << 2) >> 2] + f * n;
                g[d + (m << 2) >> 2] = n;
                m = m + 1 | 0;
            } while ((m | 0) < (e | 0))
        }
        m = e - 1 | 0;
        g[k >> 2] = +g[b + (m << 2) >> 2];
        g[l >> 2] = +g[d + (m << 2) >> 2];
        k = h;
        m = a;
        l = c[k + 4 >> 2] | 0;
        c[m >> 2] = c[k >> 2];
        c[m + 4 >> 2] = l;
        i = j;
        return
    }

    function Cb(a, b, c, d) {
        a = a | 0;
        b = b | 0;
        c = c | 0;
        d = +d;
        var e = 0.0,
            f = 0,
            h = 0.0,
            i = 0.0,
            j = 0;
        f = (c | 0) > 0;
        if (f) {
            j = 0;
            h = 0.0
        } else {
            i = 0.0 / +(c | 0);
            return +i
        }
        do {
            h = h + +g[a + (j << 2) >> 2];
            j = j + 1 | 0;
        } while ((j | 0) < (c | 0));
        e = +(c | 0);
        h = h / e;
        i = h - d;
        if (f) {
            f = 0
        } else {
            i = h;
            return +i
        }
        do {
            g[b + (f << 2) >> 2] = +g[a + (f << 2) >> 2] - (i * (+(f | 0) / e) + d);
            f = f + 1 | 0;
        } while ((f | 0) < (c | 0));
        return +h
    }

    function Db(a, b) {
        a = a | 0;
        b = b | 0;
        var d = 0,
            e = 0,
            f = 0.0,
            h = 0,
            i = 0,
            j = 0,
            k = 0.0,
            l = 0,
            m = 0.0,
            n = 0,
            o = 0.0;
        d = a + 20 | 0;
        e = c[d >> 2] | 0;
        j = (e | 0) > 0;
        if (j) {
            h = c[a + 8 >> 2] | 0;
            i = 0;
            f = 0.0;
            do {
                k = +M(+(+g[h + (i << 2) >> 2]));
                f = k > f ? k : f;
                i = i + 1 | 0;
            } while ((i | 0) < (e | 0))
        } else {
            f = 0.0
        }
        i = a + 16 | 0;
        m = +g[i >> 2];
        o = f < m ? m : f;
        h = a + 12 | 0;
        k = +g[h >> 2];
        k = +g[a + 24 >> 2] / (o < k ? k : o);
        k = k > 50.0 ? 50.0 : k;
        if (j) {
            j = a + 28 | 0;
            l = a | 0;
            n = 0;
            do {
                o = +(n | 0) / +(e | 0);
                g[b + (n << 2) >> 2] = +g[(c[l >> 2] | 0) + (n << 2) >> 2] * (k * o + +g[j >> 2] * (1.0 - o));
                n = n + 1 | 0;
                e = c[d >> 2] | 0;
            } while ((n | 0) < (e | 0));
            m = +g[i >> 2]
        } else {
            l = a | 0;
            j = a + 28 | 0
        }
        e = c[l >> 2] | 0;
        b = a + 4 | 0;
        c[l >> 2] = c[b >> 2];
        g[h >> 2] = m;
        n = a + 8 | 0;
        c[b >> 2] = c[n >> 2];
        g[i >> 2] = f;
        c[n >> 2] = e;
        g[j >> 2] = k;
        return
    }

    function Eb(a, b, c, d) {
        a = a | 0;
        b = b | 0;
        c = c | 0;
        d = +d;
        var e = 0.0,
            f = 0,
            h = 0;
        if ((c | 0) > 0) {
            f = 0
        } else {
            return +d
        }
        while (1) {
            h = a + (f << 3) | 0;
            e = +V(+(+g[h + 4 >> 2]), +(+g[h >> 2]));
            d = e - d;
            if (d < -3.1415927410125732) {
                d = d + 6.2831854820251465
            }
            if (d > 3.1415927410125732) {
                d = d + -6.2831854820251465
            }
            g[b + (f << 2) >> 2] = d / 3.1415927410125732;
            f = f + 1 | 0;
            if ((f | 0) < (c | 0)) {
                d = e
            } else {
                break
            }
        }
        return +e
    }

    function Fb(a, b, d, e, f) {
        a = a | 0;
        b = b | 0;
        d = d | 0;
        e = e | 0;
        f = f | 0;
        var h = 0,
            j = 0,
            k = 0.0,
            l = 0.0,
            m = 0,
            n = 0;
        h = i;
        m = f;
        j = i;
        i = i + 8 | 0;
        c[j >> 2] = c[m >> 2];
        c[j + 4 >> 2] = c[m + 4 >> 2];
        f = b | 0;
        l = +g[f >> 2];
        k = +g[f + 4 >> 2];
        g[d >> 2] = (l * (k - +g[j + 4 >> 2]) - k * (l - +g[j >> 2])) * .340447550238101 / (l * l + k * k);
        if ((e | 0) > 1) {
            j = 1;
            do {
                n = b + (j << 3) | 0;
                k = +g[n + 4 >> 2];
                m = j << 1;
                l = +g[n >> 2];
                g[d + (j << 2) >> 2] = (l * (k - +g[f + (m - 1 << 2) >> 2]) - k * (l - +g[f + (m - 2 << 2) >> 2])) * .340447550238101 / (k * k + l * l);
                j = j + 1 | 0;
            } while ((j | 0) < (e | 0))
        }
        j = b + (e - 1 << 3) | 0;
        n = a;
        m = c[j + 4 >> 2] | 0;
        c[n >> 2] = c[j >> 2];
        c[n + 4 >> 2] = m;
        i = h;
        return
    }

    function Gb(a, b, d, e, f, h) {
        a = a | 0;
        b = b | 0;
        d = d | 0;
        e = e | 0;
        f = f | 0;
        h = h | 0;
        var j = 0,
            k = 0,
            l = 0,
            m = 0,
            n = 0,
            o = 0.0,
            p = 0.0;
        j = i;
        m = h;
        h = i;
        i = i + 8 | 0;
        c[h >> 2] = c[m >> 2];
        c[h + 4 >> 2] = c[m + 4 >> 2];
        m = f + (e << 2) | 0;
        k = b | 0;
        g[f >> 2] = +g[k + 4 >> 2] - +g[h + 4 >> 2];
        l = (e | 0) > 1;
        do {
            if (l) {
                n = 1;
                do {
                    g[f + (n << 2) >> 2] = +g[b + (n << 3) + 4 >> 2] - +g[k + ((n << 1) - 1 << 2) >> 2];
                    n = n + 1 | 0;
                } while ((n | 0) < (e | 0));
                g[m >> 2] = +g[k >> 2] - +g[h >> 2];
                if (l) {
                    l = 1
                } else {
                    break
                }
                do {
                    g[f + (l + e << 2) >> 2] = +g[b + (l << 3) >> 2] - +g[k + ((l << 1) - 2 << 2) >> 2];
                    l = l + 1 | 0;
                } while ((l | 0) < (e | 0))
            } else {
                g[m >> 2] = +g[k >> 2] - +g[h >> 2]
            }
        } while (0);
        k = (e | 0) > 0;
        do {
            if (k) {
                l = 0;
                do {
                    n = b + (l << 3) | 0;
                    g[d + (l << 2) >> 2] = +g[n >> 2] * +g[f + (l << 2) >> 2] - +g[n + 4 >> 2] * +g[f + (l + e << 2) >> 2];
                    l = l + 1 | 0;
                } while ((l | 0) < (e | 0));
                if (k) {
                    l = 0
                } else {
                    break
                }
                do {
                    n = b + (l << 3) | 0;
                    p = +g[n >> 2];
                    o = +g[n + 4 >> 2];
                    g[f + (l << 2) >> 2] = p * p + o * o;
                    l = l + 1 | 0;
                } while ((l | 0) < (e | 0));
                if (k) {
                    k = 0
                } else {
                    break
                }
                do {
                    o = +g[f + (k << 2) >> 2];
                    l = d + (k << 2) | 0;
                    if (o != 0.0) {
                        o = +g[l >> 2] * .340447550238101 / o
                    } else {
                        o = 0.0
                    }
                    g[l >> 2] = o;
                    k = k + 1 | 0;
                } while ((k | 0) < (e | 0))
            }
        } while (0);
        h = b + (e - 1 << 3) | 0;
        n = a;
        m = c[h + 4 >> 2] | 0;
        c[n >> 2] = c[h >> 2];
        c[n + 4 >> 2] = m;
        i = j;
        return
    }

    function Hb(a, b, d, e, f, h) {
        a = a | 0;
        b = b | 0;
        d = d | 0;
        e = +e;
        f = f | 0;
        h = +h;
        var i = 0.0;
        i = 1.0 / +(f | 0);
        e = i / (i + e);
        f = (g[k >> 2] = h, c[k >> 2] | 0);
        if ((f & 2139095040 | 0) == 2139095040) {
            i = (f & 8388607 | 0) != 0 ? 0.0 : h
        } else {
            i = h
        }
        h = 1.0 - e;
        i = h * i + e * +g[a >> 2];
        g[b >> 2] = i;
        if ((d | 0) > 1) {
            f = 1
        } else {
            f = d - 1 | 0;
            f = b + (f << 2) | 0;
            i = +g[f >> 2];
            return +i
        }
        do {
            i = e * +g[a + (f << 2) >> 2] + h * i;
            g[b + (f << 2) >> 2] = i;
            f = f + 1 | 0;
        } while ((f | 0) < (d | 0));
        f = d - 1 | 0;
        f = b + (f << 2) | 0;
        i = +g[f >> 2];
        return +i
    }

    function Ib(a, b, c, d) {
        a = a | 0;
        b = b | 0;
        c = c | 0;
        d = d | 0;
        var e = 0,
            f = 0,
            h = 0,
            i = 0,
            j = 0.0;
        f = (d | 0) == 44100;
        i = (d | 0) == 8e3;
        h = (d | 0) == 11025;
        e = h ? 1776 : i ? 144 : f ? 1280 : 472;
        d = h ? 81 : i ? 81 : f ? 123 : (d | 0) == 48e3 ? 201 : 0;
        if ((d | 0) == 0) {
            i = 0;
            return i | 0
        }
        c = c - d | 0;
        if ((c | 0) > 0) {
            f = 0
        } else {
            i = 0;
            return i | 0
        }
        do {
            j = 0.0;
            h = 0;
            do {
                j = j + +g[e + (h << 2) >> 2] * +g[a + (h + f << 2) >> 2];
                h = h + 1 | 0;
            } while ((h | 0) < (d | 0));
            g[b + (f << 2) >> 2] = j;
            f = f + 1 | 0;
        } while ((f | 0) < (c | 0));
        return c | 0
    }

    function Jb(a, b, c, d) {
        a = a | 0;
        b = b | 0;
        c = c | 0;
        d = +d;
        var e = 0.0,
            f = 0,
            h = 0.0;
        if ((c | 0) <= 0) {
            return
        }
        e = -0.0 - d;
        f = 0;
        do {
            h = +g[a + (f << 2) >> 2];
            h = h > d ? d : h;
            g[b + (f << 2) >> 2] = h < e ? e : h;
            f = f + 1 | 0;
        } while ((f | 0) < (c | 0));
        return
    }

    function Kb(a, b, c, d) {
        a = a | 0;
        b = b | 0;
        c = c | 0;
        d = +d;
        var e = 0;
        if ((c | 0) > 0) {
            e = 0
        } else {
            return
        }
        do {
            g[b + (e << 2) >> 2] = +g[a + (e << 2) >> 2] * d;
            e = e + 1 | 0;
        } while ((e | 0) < (c | 0));
        return
    }

    function Lb(a) {
        a = a | 0;
        var b = 0,
            c = 0;
        c = -1;
        b = 0;
        while (1) {
            if ((1 << b & a | 0) != 0) {
                if ((c | 0) == -1) {
                    c = b
                } else {
                    c = -1;
                    a = 5;
                    break
                }
            }
            b = b + 1 | 0;
            if ((b | 0) >= 31) {
                a = 5;
                break
            }
        }
        if ((a | 0) == 5) {
            return c | 0
        }
        return 0
    }

    function Mb(a) {
        a = a | 0;
        var b = 0,
            c = 0;
        c = 0;
        while (1) {
            b = 1 << c;
            c = c + 1 | 0;
            if ((b | 0) > (a | 0)) {
                break
            }
            if ((c | 0) >= 31) {
                b = -1;
                break
            }
        }
        return b | 0
    }

    function Nb(a, b, c, d) {
        a = a | 0;
        b = b | 0;
        c = c | 0;
        d = d | 0;
        var e = 0.0,
            f = 0,
            h = 0,
            i = 0.0,
            j = 0.0,
            k = 0;
        if ((d | 0) == 1) {
            d = 6
        } else if ((d | 0) == 0) {
            d = 2
        } else {
            d = 4
        }
        if ((c | 0) <= 0) {
            return
        }
        e = +(c - 1 | 0);
        f = 0;
        do {
            k = a + (f << 3) | 0;
            j = +g[k >> 2];
            i = +(f | 0) / e * 2.0 + 1.0;
            h = b + (f << 3) | 0;
            g[h >> 2] = j * +Pa[d & 7](i);
            j = +g[k + 4 >> 2];
            g[h + 4 >> 2] = j * +Pa[d & 7](i);
            f = f + 1 | 0;
        } while ((f | 0) < (c | 0));
        return
    }

    function Ob(a, b, c, d) {
        a = a | 0;
        b = b | 0;
        c = c | 0;
        d = d | 0;
        var e = 0.0,
            f = 0,
            h = 0.0;
        if ((d | 0) == 1) {
            d = 6
        } else if ((d | 0) == 0) {
            d = 2
        } else {
            d = 4
        }
        if ((c | 0) <= 0) {
            return
        }
        e = +(c - 1 | 0);
        f = 0;
        do {
            h = +g[a + (f << 2) >> 2];
            g[b + (f << 2) >> 2] = h * +Pa[d & 7](+(f | 0) / e * 2.0 + 1.0);
            f = f + 1 | 0;
        } while ((f | 0) < (c | 0));
        return
    }

    function Pb(a, b, c, d) {
        a = a | 0;
        b = b | 0;
        c = c | 0;
        d = +d;
        var e = 0,
            f = 0,
            h = 0.0,
            i = 0.0,
            j = 0;
        e = (c | 0) > 0;
        if (e) {
            f = 0
        } else {
            return
        }
        do {
            j = a + (f << 3) | 0;
            i = +g[j >> 2];
            h = +g[j + 4 >> 2];
            g[b + (f << 2) >> 2] = i * i + h * h;
            f = f + 1 | 0;
        } while ((f | 0) < (c | 0));
        if (e) {
            a = 0
        } else {
            return
        }
        do {
            j = b + (a << 2) | 0;
            g[j >> 2] = +za(+(+g[j >> 2]));
            a = a + 1 | 0;
        } while ((a | 0) < (c | 0));
        if (e) {
            e = 0
        } else {
            return
        }
        do {
            j = b + (e << 2) | 0;
            g[j >> 2] = +g[j >> 2] * 10.0 + d;
            e = e + 1 | 0;
        } while ((e | 0) < (c | 0));
        return
    }

    function Qb(a, b, c) {
        a = a | 0;
        b = b | 0;
        c = c | 0;
        var e = 0;
        if ((c | 0) > 0) {
            e = 0
        } else {
            return
        }
        do {
            g[b + (e << 2) >> 2] = +((d[a + e | 0] | 0) >>> 0) / 127.5 + -1.0;
            e = e + 1 | 0;
        } while ((e | 0) < (c | 0));
        return
    }

    function Rb(b, c, d) {
        b = b | 0;
        c = c | 0;
        d = d | 0;
        var e = 0;
        if ((d | 0) > 0) {
            e = 0
        } else {
            return
        }
        do {
            a[c + e | 0] = ~~(+g[b + (e << 2) >> 2] * 255.0 * .5 + 128.0);
            e = e + 1 | 0;
        } while ((e | 0) < (d | 0));
        return
    }

    function Sb(a, c, d) {
        a = a | 0;
        c = c | 0;
        d = d | 0;
        var e = 0;
        if ((d | 0) > 0) {
            e = 0
        } else {
            return
        }
        do {
            g[c + (e << 2) >> 2] = +(b[a + (e << 1) >> 1] | 0) / 32767.0;
            e = e + 1 | 0;
        } while ((e | 0) < (d | 0));
        return
    }

    function Tb(a, c, d) {
        a = a | 0;
        c = c | 0;
        d = d | 0;
        var e = 0;
        if ((d | 0) > 0) {
            e = 0
        } else {
            return
        }
        do {
            b[c + (e << 1) >> 1] = ~~(+g[a + (e << 2) >> 2] * 32767.0);
            e = e + 1 | 0;
        } while ((e | 0) < (d | 0));
        return
    }

    function Ub(a, b, d, e, f) {
        a = a | 0;
        b = b | 0;
        d = d | 0;
        e = e | 0;
        f = +f;
        var h = 0,
            j = 0.0,
            k = 0.0,
            l = 0.0,
            m = 0.0,
            n = 0.0,
            o = 0,
            p = 0,
            q = 0,
            r = 0;
        h = i;
        o = e;
        e = i;
        i = i + 12 | 0;
        i = i + 7 & -8;
        c[e >> 2] = c[o >> 2];
        c[e + 4 >> 2] = c[o + 4 >> 2];
        c[e + 8 >> 2] = c[o + 8 >> 2];
        j = f;
        if ((d | 0) > 0) {
            m = +Q(j);
            n = +P(j);
            k = +g[e + 4 >> 2];
            l = +g[e >> 2];
            o = 0;
            while (1) {
                r = a + (o << 3) | 0;
                q = r + 4 | 0;
                p = b + (o << 3) | 0;
                g[p >> 2] = n * +g[r >> 2] - m * +g[q >> 2];
                g[p + 4 >> 2] = m * +g[r >> 2] + n * +g[q >> 2];
                j = n * k - m * l;
                o = o + 1 | 0;
                if ((o | 0) < (d | 0)) {
                    m = m * k + n * l;
                    n = j
                } else {
                    break
                }
            }
        }
        f = +(d | 0) * +g[e + 8 >> 2] * 3.1415927410125732 + f;
        if (f > 3.1415927410125732) {
            do {
                f = f + -6.2831854820251465;
            } while (f > 3.1415927410125732)
        }
        if (f >= -3.1415927410125732) {
            n = f;
            i = h;
            return +n
        }
        do {
            f = f + 6.2831854820251465;
        } while (f < -3.1415927410125732);
        i = h;
        return +f
    }

    function Vb(a, b) {
        a = a | 0;
        b = +b;
        var c = 0.0,
            d = 0.0;
        b = b * 2.0;
        d = b * 3.1415927410125732;
        c = +P(d);
        g[a >> 2] = +Q(d);
        g[a + 4 >> 2] = c;
        g[a + 8 >> 2] = b;
        return
    }

    function Wb(a) {
        a = a | 0;
        var b = 0,
            d = 0.0,
            e = 0.0,
            f = 0.0,
            j = 0.0,
            k = 0.0,
            l = 0,
            m = 0.0,
            n = 0.0,
            o = 0.0,
            p = 0,
            q = 0.0,
            r = 0;
        b = i;
        l = a;
        p = i;
        i = i + 12 | 0;
        i = i + 7 & -8;
        c[p >> 2] = c[l >> 2];
        c[p + 4 >> 2] = c[l + 4 >> 2];
        c[p + 8 >> 2] = c[l + 8 >> 2];
        e = +g[p + 8 >> 2];
        a = ~~(2.0 / e + 1.0);
        oa(2112, (l = i, i = i + 1 | 0, i = i + 7 & -8, c[l >> 2] = 0, l) | 0) | 0;
        i = l;
        j = +g[p + 4 >> 2];
        f = +g[p >> 2];
        e = e * 3.1415927410125732;
        d = +(a | 0);
        m = 0.0;
        q = 1.0;
        n = 0.0;
        p = 0;
        o = 0.0;
        l = 0;
        while (1) {
            k = q * j - m * f;
            m = m * j + q * f;
            n = n + e;
            if (n > 6.2831854820251465) {
                do {
                    n = n + -6.2831854820251465;
                } while (n > 6.2831854820251465)
            }
            r = ((l >>> 0) % 1e4 | 0 | 0) == 0;
            p = r ? a : p;
            o = r ? 0.0 : o;
            do {
                if ((p | 0) == 0) {
                    p = 0
                } else {
                    o = o + +M(+(k - +P(n)));
                    p = p - 1 | 0;
                    if ((p | 0) != 0) {
                        break
                    }
                    oa(2104, (p = i, i = i + 8 | 0, h[p >> 3] = o / d, p) | 0) | 0;
                    i = p;
                    p = 0
                }
            } while (0);
            l = l + 1 | 0;
            if (l >>> 0 < 5e5 >>> 0) {
                q = k
            } else {
                break
            }
        }
        Fa(8) | 0;
        i = b;
        return
    }

    function Xb(a, b, c) {
        a = a | 0;
        b = +b;
        c = c | 0;
        var d = 0.0,
            e = 0.0;
        b = +(c | 0) * b * 2.0;
        e = b * 3.1415927410125732;
        d = +P(e);
        g[a >> 2] = +Q(e);
        g[a + 4 >> 2] = d;
        g[a + 8 >> 2] = b;
        return
    }

    function Yb(a, b, d, e, f, h, j) {
        a = a | 0;
        b = b | 0;
        d = d | 0;
        e = e | 0;
        f = f | 0;
        h = h | 0;
        j = j | 0;
        var k = 0,
            l = 0,
            m = 0,
            n = 0.0,
            o = 0.0,
            p = 0.0,
            q = 0.0,
            r = 0.0,
            s = 0,
            t = 0,
            u = 0.0,
            v = 0,
            w = 0,
            x = 0;
        l = i;
        k = f;
        f = i;
        i = i + 12 | 0;
        i = i + 7 & -8;
        c[f >> 2] = c[k >> 2];
        c[f + 4 >> 2] = c[k + 4 >> 2];
        c[f + 8 >> 2] = c[k + 8 >> 2];
        k = j;
        j = i;
        i = i + 12 | 0;
        i = i + 7 & -8;
        c[j >> 2] = c[k >> 2];
        c[j + 4 >> 2] = c[k + 4 >> 2];
        c[j + 8 >> 2] = c[k + 8 >> 2];
        k = j + 4 | 0;
        n = +g[k >> 2];
        o = n;
        m = j | 0;
        t = c[m >> 2] | 0;
        if ((t | 0) < (e | 0)) {
            p = +Q(o);
            o = +P(o);
            q = +g[f + 4 >> 2];
            r = +g[f >> 2];
            s = 0;
            while (1) {
                x = b + (t << 3) | 0;
                w = x + 4 | 0;
                v = d + (s << 3) | 0;
                g[v >> 2] = o * +g[x >> 2] - p * +g[w >> 2];
                g[v + 4 >> 2] = p * +g[x >> 2] + o * +g[w >> 2];
                s = s + 1 | 0;
                u = o * q - p * r;
                t = t + h | 0;
                if ((t | 0) < (e | 0)) {
                    p = p * q + o * r;
                    o = u
                } else {
                    break
                }
            }
        } else {
            s = 0
        }
        c[m >> 2] = t - e;
        n = n + +(s | 0) * +g[f + 8 >> 2] * 3.1415927410125732;
        g[k >> 2] = n;
        c[j + 8 >> 2] = s;
        if (n > 3.1415927410125732) {
            do {
                n = n + -6.2831854820251465;
            } while (n > 3.1415927410125732);
            g[k >> 2] = n
        }
        if (n >= -3.1415927410125732) {
            x = a;
            w = j;
            c[x >> 2] = c[w >> 2];
            c[x + 4 >> 2] = c[w + 4 >> 2];
            c[x + 8 >> 2] = c[w + 8 >> 2];
            i = l;
            return
        }
        do {
            n = n + 6.2831854820251465;
        } while (n < -3.1415927410125732);
        g[k >> 2] = n;
        x = a;
        w = j;
        c[x >> 2] = c[w >> 2];
        c[x + 4 >> 2] = c[w + 4 >> 2];
        c[x + 8 >> 2] = c[w + 8 >> 2];
        i = l;
        return
    }

    function Zb(a, b, c, d, e, f, h, i, j, k, l) {
        a = a | 0;
        b = b | 0;
        c = c | 0;
        d = +d;
        e = +e;
        f = +f;
        h = +h;
        i = i | 0;
        j = j | 0;
        k = +k;
        l = +l;
        var m = 0.0,
            n = 0,
            o = 0,
            p = 0,
            q = 0.0,
            r = 0.0,
            s = 0,
            t = 0.0;
        g[b >> 2] = +g[a >> 2] * l;
        if ((c | 0) <= 1) {
            t = l;
            return +t
        }
        o = 0;
        m = l;
        q = d / l;
        p = 0;
        n = 1;
        do {
            l = +g[a + (n << 2) >> 2];
            t = +M(+l);
            r = d / t - m;
            if (l != 0.0) {
                do {
                    if (r < 0.0) {
                        s = q < t;
                        o = s ? j : o;
                        q = s ? t : q;
                        if (o << 16 >> 16 > 0) {
                            r = 0.0;
                            o = o - 1 & 65535;
                            break
                        } else {
                            r = r * e;
                            p = i;
                            break
                        }
                    } else {
                        if (p << 16 >> 16 > 0) {
                            r = 0.0;
                            p = p - 1 & 65535;
                            break
                        } else {
                            r = r * f;
                            break
                        }
                    }
                } while (0);
                r = m + r
            } else {
                r = m
            }
            r = r > h ? h : r;
            m = m + (r < 0.0 ? 0.0 : r) - m * k;
            g[b + (n << 2) >> 2] = l * m;
            n = n + 1 | 0;
        } while ((n | 0) < (c | 0));
        return +m
    }

    function _b(d, e, f, g, h) {
        d = d | 0;
        e = e | 0;
        f = f | 0;
        g = g | 0;
        h = h | 0;
        var j = 0,
            k = 0,
            l = 0,
            m = 0,
            n = 0,
            o = 0,
            p = 0,
            q = 0,
            r = 0,
            s = 0,
            t = 0,
            u = 0,
            v = 0;
        j = i;
        k = h;
        h = i;
        i = i + 8 | 0;
        c[h >> 2] = c[k >> 2];
        c[h + 4 >> 2] = c[k + 4 >> 2];
        k = (g | 0) / 2 | 0;
        if ((g | 0) <= 1) {
            u = h;
            v = d;
            s = u | 0;
            s = c[s >> 2] | 0;
            u = u + 4 | 0;
            u = c[u >> 2] | 0;
            t = v | 0;
            c[t >> 2] = s;
            v = v + 4 | 0;
            c[v >> 2] = u;
            i = j;
            return
        }
        g = h + 4 | 0;
        l = h | 0;
        m = 0;
        p = c[g >> 2] | 0;
        o = c[l >> 2] | 0;
        while (1) {
            q = m << 1;
            n = (b[e + (q << 1) >> 1] | 0) - p | 0;
            r = c[2168 + (o << 2) >> 2] | 0;
            s = (n | 0) < 0 ? -n | 0 : n;
            n = n >> 31 & 8;
            if ((s | 0) < (r | 0)) {
                t = s
            } else {
                n = n | 4;
                t = s - r | 0
            }
            s = r >> 1;
            if ((t | 0) >= (s | 0)) {
                n = n | 2;
                t = t - s | 0
            }
            u = r >> 2;
            if ((t | 0) < (u | 0)) {
                n = n & 255
            } else {
                n = (n | 1) & 255
            }
            t = n & 255;
            r = (r >> 3) + ((t & 1 | 0) == 0 ? 0 : u) + ((t & 2 | 0) == 0 ? 0 : s) + ((t & 4 | 0) == 0 ? 0 : r) | 0;
            p = ((t & 8 | 0) == 0 ? r : -r | 0) + p | 0;
            if ((p | 0) > 32767) {
                p = 32767
            } else {
                p = (p | 0) < -32768 ? -32768 : p
            }
            o = (c[80 + (t << 2) >> 2] | 0) + o | 0;
            if ((o | 0) < 0) {
                r = 0
            } else {
                r = (o | 0) > 88 ? 88 : o
            }
            o = f + m | 0;
            a[o] = n;
            s = (b[e + ((q | 1) << 1) >> 1] | 0) - p | 0;
            q = c[2168 + (r << 2) >> 2] | 0;
            u = (s | 0) < 0 ? -s | 0 : s;
            s = s >> 31 & 8;
            if ((u | 0) >= (q | 0)) {
                s = s | 4;
                u = u - q | 0
            }
            t = q >> 1;
            if ((u | 0) >= (t | 0)) {
                s = s | 2;
                u = u - t | 0
            }
            v = q >> 2;
            if ((u | 0) < (v | 0)) {
                s = s & 255
            } else {
                s = (s | 1) & 255
            }
            u = s & 255;
            q = (q >> 3) + ((u & 1 | 0) == 0 ? 0 : v) + ((u & 2 | 0) == 0 ? 0 : t) + ((u & 4 | 0) == 0 ? 0 : q) | 0;
            p = ((u & 8 | 0) == 0 ? q : -q | 0) + p | 0;
            if ((p | 0) > 32767) {
                p = 32767
            } else {
                p = (p | 0) < -32768 ? -32768 : p
            }
            q = (c[80 + (u << 2) >> 2] | 0) + r | 0;
            if ((q | 0) < 0) {
                q = 0
            } else {
                q = (q | 0) > 88 ? 88 : q
            }
            m = m + 1 | 0;
            a[o] = n | s << 4;
            if ((m | 0) < (k | 0)) {
                o = q
            } else {
                break
            }
        }
        c[g >> 2] = p;
        c[l >> 2] = q;
        u = h;
        v = d;
        s = u | 0;
        s = c[s >> 2] | 0;
        u = u + 4 | 0;
        u = c[u >> 2] | 0;
        t = v | 0;
        c[t >> 2] = s;
        v = v + 4 | 0;
        c[v >> 2] = u;
        i = j;
        return
    }

    function $b(e, f, g, h, j) {
        e = e | 0;
        f = f | 0;
        g = g | 0;
        h = h | 0;
        j = j | 0;
        var k = 0,
            l = 0,
            m = 0,
            n = 0,
            o = 0,
            p = 0,
            q = 0,
            r = 0,
            s = 0,
            t = 0,
            u = 0;
        n = i;
        u = j;
        j = i;
        i = i + 8 | 0;
        c[j >> 2] = c[u >> 2];
        c[j + 4 >> 2] = c[u + 4 >> 2];
        if ((h | 0) <= 0) {
            t = j;
            u = e;
            r = t | 0;
            r = c[r >> 2] | 0;
            t = t + 4 | 0;
            t = c[t >> 2] | 0;
            s = u | 0;
            c[s >> 2] = r;
            u = u + 4 | 0;
            c[u >> 2] = t;
            i = n;
            return
        }
        k = j | 0;
        l = j + 4 | 0;
        m = 0;
        o = 0;
        q = c[k >> 2] | 0;
        r = c[l >> 2] | 0;
        while (1) {
            p = f + o | 0;
            t = c[2168 + (q << 2) >> 2] | 0;
            u = t >> 3;
            s = a[p] & 15;
            if ((s & 1 | 0) != 0) {
                u = u + (t >> 2) | 0
            }
            if ((s & 2 | 0) != 0) {
                u = u + (t >> 1) | 0
            }
            t = u + ((s & 4 | 0) == 0 ? 0 : t) | 0;
            u = ((s & 8 | 0) == 0 ? t : -t | 0) + r | 0;
            if ((u | 0) > 32767) {
                t = 32767;
                r = 32767
            } else {
                r = (u | 0) < -32768;
                t = r ? -32768 : u & 65535;
                r = r ? -32768 : u
            }
            q = (c[80 + (s << 2) >> 2] | 0) + q | 0;
            if ((q | 0) < 0) {
                q = 0
            } else {
                q = (q | 0) > 88 ? 88 : q
            }
            b[g + (m << 1) >> 1] = t;
            s = c[2168 + (q << 2) >> 2] | 0;
            t = s >> 3;
            p = (d[p] | 0) >>> 4 & 255;
            if ((p & 1 | 0) != 0) {
                t = t + (s >> 2) | 0
            }
            if ((p & 2 | 0) != 0) {
                t = t + (s >> 1) | 0
            }
            s = t + ((p & 4 | 0) == 0 ? 0 : s) | 0;
            r = ((p & 8 | 0) == 0 ? s : -s | 0) + r | 0;
            if ((r | 0) > 32767) {
                s = 32767;
                r = 32767
            } else {
                t = (r | 0) < -32768;
                s = t ? -32768 : r & 65535;
                r = t ? -32768 : r
            }
            p = (c[80 + (p << 2) >> 2] | 0) + q | 0;
            if ((p | 0) < 0) {
                q = 0
            } else {
                q = (p | 0) > 88 ? 88 : p
            }
            b[g + ((m | 1) << 1) >> 1] = s;
            o = o + 1 | 0;
            if ((o | 0) < (h | 0)) {
                m = m + 2 | 0
            } else {
                break
            }
        }
        c[k >> 2] = q;
        c[l >> 2] = r;
        t = j;
        u = e;
        r = t | 0;
        r = c[r >> 2] | 0;
        t = t + 4 | 0;
        t = c[t >> 2] | 0;
        s = u | 0;
        c[s >> 2] = r;
        u = u + 4 | 0;
        c[u >> 2] = t;
        i = n;
        return
    }

    function ac(a) {
        a = a | 0;
        var b = 0,
            d = 0;
        b = i;
        d = c[a >> 2] | 0;
        Na[c[c[d >> 2] >> 2] & 1](d, c[a + 4 >> 2] | 0);
        i = b;
        return
    }

    function bc(a) {
        a = a | 0;
        var b = 0,
            d = 0,
            e = 0,
            f = 0,
            g = 0,
            h = 0,
            i = 0,
            j = 0,
            k = 0,
            l = 0,
            m = 0,
            n = 0,
            o = 0,
            p = 0,
            q = 0;
        do {
            if (a >>> 0 < 245 >>> 0) {
                if (a >>> 0 < 11 >>> 0) {
                    a = 16
                } else {
                    a = a + 11 & -8
                }
                f = a >>> 3;
                e = c[638] | 0;
                b = e >>> (f >>> 0);
                if ((b & 3 | 0) != 0) {
                    h = (b & 1 ^ 1) + f | 0;
                    a = h << 1;
                    d = 2592 + (a << 2) | 0;
                    a = 2592 + (a + 2 << 2) | 0;
                    g = c[a >> 2] | 0;
                    f = g + 8 | 0;
                    b = c[f >> 2] | 0;
                    do {
                        if ((d | 0) == (b | 0)) {
                            c[638] = e & ~(1 << h)
                        } else {
                            if (b >>> 0 < (c[642] | 0) >>> 0) {
                                ma();
                                return 0
                            }
                            e = b + 12 | 0;
                            if ((c[e >> 2] | 0) == (g | 0)) {
                                c[e >> 2] = d;
                                c[a >> 2] = b;
                                break
                            } else {
                                ma();
                                return 0
                            }
                        }
                    } while (0);
                    q = h << 3;
                    c[g + 4 >> 2] = q | 3;
                    q = g + (q | 4) | 0;
                    c[q >> 2] = c[q >> 2] | 1;
                    q = f;
                    return q | 0
                }
                if (a >>> 0 <= (c[640] | 0) >>> 0) {
                    break
                }
                if ((b | 0) != 0) {
                    i = 2 << f;
                    i = b << f & (i | -i);
                    i = (i & -i) - 1 | 0;
                    b = i >>> 12 & 16;
                    i = i >>> (b >>> 0);
                    h = i >>> 5 & 8;
                    i = i >>> (h >>> 0);
                    f = i >>> 2 & 4;
                    i = i >>> (f >>> 0);
                    g = i >>> 1 & 2;
                    i = i >>> (g >>> 0);
                    d = i >>> 1 & 1;
                    d = (h | b | f | g | d) + (i >>> (d >>> 0)) | 0;
                    i = d << 1;
                    g = 2592 + (i << 2) | 0;
                    i = 2592 + (i + 2 << 2) | 0;
                    f = c[i >> 2] | 0;
                    b = f + 8 | 0;
                    h = c[b >> 2] | 0;
                    do {
                        if ((g | 0) == (h | 0)) {
                            c[638] = e & ~(1 << d)
                        } else {
                            if (h >>> 0 < (c[642] | 0) >>> 0) {
                                ma();
                                return 0
                            }
                            e = h + 12 | 0;
                            if ((c[e >> 2] | 0) == (f | 0)) {
                                c[e >> 2] = g;
                                c[i >> 2] = h;
                                break
                            } else {
                                ma();
                                return 0
                            }
                        }
                    } while (0);
                    q = d << 3;
                    d = q - a | 0;
                    c[f + 4 >> 2] = a | 3;
                    e = f + a | 0;
                    c[f + (a | 4) >> 2] = d | 1;
                    c[f + q >> 2] = d;
                    f = c[640] | 0;
                    if ((f | 0) != 0) {
                        a = c[643] | 0;
                        i = f >>> 3;
                        g = i << 1;
                        f = 2592 + (g << 2) | 0;
                        h = c[638] | 0;
                        i = 1 << i;
                        do {
                            if ((h & i | 0) == 0) {
                                c[638] = h | i;
                                h = f;
                                g = 2592 + (g + 2 << 2) | 0
                            } else {
                                g = 2592 + (g + 2 << 2) | 0;
                                h = c[g >> 2] | 0;
                                if (h >>> 0 >= (c[642] | 0) >>> 0) {
                                    break
                                }
                                ma();
                                return 0
                            }
                        } while (0);
                        c[g >> 2] = a;
                        c[h + 12 >> 2] = a;
                        c[a + 8 >> 2] = h;
                        c[a + 12 >> 2] = f
                    }
                    c[640] = d;
                    c[643] = e;
                    q = b;
                    return q | 0
                }
                b = c[639] | 0;
                if ((b | 0) == 0) {
                    break
                }
                e = (b & -b) - 1 | 0;
                p = e >>> 12 & 16;
                e = e >>> (p >>> 0);
                o = e >>> 5 & 8;
                e = e >>> (o >>> 0);
                q = e >>> 2 & 4;
                e = e >>> (q >>> 0);
                b = e >>> 1 & 2;
                e = e >>> (b >>> 0);
                d = e >>> 1 & 1;
                d = c[2856 + ((o | p | q | b | d) + (e >>> (d >>> 0)) << 2) >> 2] | 0;
                e = d;
                b = d;
                d = (c[d + 4 >> 2] & -8) - a | 0;
                while (1) {
                    h = c[e + 16 >> 2] | 0;
                    if ((h | 0) == 0) {
                        h = c[e + 20 >> 2] | 0;
                        if ((h | 0) == 0) {
                            break
                        }
                    }
                    g = (c[h + 4 >> 2] & -8) - a | 0;
                    f = g >>> 0 < d >>> 0;
                    e = h;
                    b = f ? h : b;
                    d = f ? g : d
                }
                f = b;
                h = c[642] | 0;
                if (f >>> 0 < h >>> 0) {
                    ma();
                    return 0
                }
                q = f + a | 0;
                e = q;
                if (f >>> 0 >= q >>> 0) {
                    ma();
                    return 0
                }
                g = c[b + 24 >> 2] | 0;
                i = c[b + 12 >> 2] | 0;
                do {
                    if ((i | 0) == (b | 0)) {
                        j = b + 20 | 0;
                        i = c[j >> 2] | 0;
                        if ((i | 0) == 0) {
                            j = b + 16 | 0;
                            i = c[j >> 2] | 0;
                            if ((i | 0) == 0) {
                                i = 0;
                                break
                            }
                        }
                        while (1) {
                            l = i + 20 | 0;
                            k = c[l >> 2] | 0;
                            if ((k | 0) != 0) {
                                i = k;
                                j = l;
                                continue
                            }
                            k = i + 16 | 0;
                            l = c[k >> 2] | 0;
                            if ((l | 0) == 0) {
                                break
                            } else {
                                i = l;
                                j = k
                            }
                        }
                        if (j >>> 0 < h >>> 0) {
                            ma();
                            return 0
                        } else {
                            c[j >> 2] = 0;
                            break
                        }
                    } else {
                        j = c[b + 8 >> 2] | 0;
                        if (j >>> 0 < h >>> 0) {
                            ma();
                            return 0
                        }
                        h = j + 12 | 0;
                        if ((c[h >> 2] | 0) != (b | 0)) {
                            ma();
                            return 0
                        }
                        k = i + 8 | 0;
                        if ((c[k >> 2] | 0) == (b | 0)) {
                            c[h >> 2] = i;
                            c[k >> 2] = j;
                            break
                        } else {
                            ma();
                            return 0
                        }
                    }
                } while (0);
                a: do {
                    if ((g | 0) != 0) {
                        j = b + 28 | 0;
                        h = 2856 + (c[j >> 2] << 2) | 0;
                        do {
                            if ((b | 0) == (c[h >> 2] | 0)) {
                                c[h >> 2] = i;
                                if ((i | 0) != 0) {
                                    break
                                }
                                c[639] = c[639] & ~(1 << c[j >> 2]);
                                break a
                            } else {
                                if (g >>> 0 < (c[642] | 0) >>> 0) {
                                    ma();
                                    return 0
                                }
                                h = g + 16 | 0;
                                if ((c[h >> 2] | 0) == (b | 0)) {
                                    c[h >> 2] = i
                                } else {
                                    c[g + 20 >> 2] = i
                                }
                                if ((i | 0) == 0) {
                                    break a
                                }
                            }
                        } while (0);
                        if (i >>> 0 < (c[642] | 0) >>> 0) {
                            ma();
                            return 0
                        }
                        c[i + 24 >> 2] = g;
                        g = c[b + 16 >> 2] | 0;
                        do {
                            if ((g | 0) != 0) {
                                if (g >>> 0 < (c[642] | 0) >>> 0) {
                                    ma();
                                    return 0
                                } else {
                                    c[i + 16 >> 2] = g;
                                    c[g + 24 >> 2] = i;
                                    break
                                }
                            }
                        } while (0);
                        g = c[b + 20 >> 2] | 0;
                        if ((g | 0) == 0) {
                            break
                        }
                        if (g >>> 0 < (c[642] | 0) >>> 0) {
                            ma();
                            return 0
                        } else {
                            c[i + 20 >> 2] = g;
                            c[g + 24 >> 2] = i;
                            break
                        }
                    }
                } while (0);
                if (d >>> 0 < 16 >>> 0) {
                    q = d + a | 0;
                    c[b + 4 >> 2] = q | 3;
                    q = f + (q + 4) | 0;
                    c[q >> 2] = c[q >> 2] | 1
                } else {
                    c[b + 4 >> 2] = a | 3;
                    c[f + (a | 4) >> 2] = d | 1;
                    c[f + (d + a) >> 2] = d;
                    f = c[640] | 0;
                    if ((f | 0) != 0) {
                        a = c[643] | 0;
                        h = f >>> 3;
                        g = h << 1;
                        f = 2592 + (g << 2) | 0;
                        i = c[638] | 0;
                        h = 1 << h;
                        do {
                            if ((i & h | 0) == 0) {
                                c[638] = i | h;
                                h = f;
                                g = 2592 + (g + 2 << 2) | 0
                            } else {
                                g = 2592 + (g + 2 << 2) | 0;
                                h = c[g >> 2] | 0;
                                if (h >>> 0 >= (c[642] | 0) >>> 0) {
                                    break
                                }
                                ma();
                                return 0
                            }
                        } while (0);
                        c[g >> 2] = a;
                        c[h + 12 >> 2] = a;
                        c[a + 8 >> 2] = h;
                        c[a + 12 >> 2] = f
                    }
                    c[640] = d;
                    c[643] = e
                }
                q = b + 8 | 0;
                return q | 0
            } else {
                if (a >>> 0 > 4294967231 >>> 0) {
                    a = -1;
                    break
                }
                b = a + 11 | 0;
                a = b & -8;
                f = c[639] | 0;
                if ((f | 0) == 0) {
                    break
                }
                e = -a | 0;
                b = b >>> 8;
                do {
                    if ((b | 0) == 0) {
                        g = 0
                    } else {
                        if (a >>> 0 > 16777215 >>> 0) {
                            g = 31;
                            break
                        }
                        p = (b + 1048320 | 0) >>> 16 & 8;
                        q = b << p;
                        o = (q + 520192 | 0) >>> 16 & 4;
                        q = q << o;
                        g = (q + 245760 | 0) >>> 16 & 2;
                        g = 14 - (o | p | g) + (q << g >>> 15) | 0;
                        g = a >>> ((g + 7 | 0) >>> 0) & 1 | g << 1
                    }
                } while (0);
                h = c[2856 + (g << 2) >> 2] | 0;
                b: do {
                    if ((h | 0) == 0) {
                        b = 0;
                        j = 0
                    } else {
                        if ((g | 0) == 31) {
                            i = 0
                        } else {
                            i = 25 - (g >>> 1) | 0
                        }
                        b = 0;
                        i = a << i;
                        j = 0;
                        while (1) {
                            l = c[h + 4 >> 2] & -8;
                            k = l - a | 0;
                            if (k >>> 0 < e >>> 0) {
                                if ((l | 0) == (a | 0)) {
                                    b = h;
                                    e = k;
                                    j = h;
                                    break b
                                } else {
                                    b = h;
                                    e = k
                                }
                            }
                            k = c[h + 20 >> 2] | 0;
                            h = c[h + 16 + (i >>> 31 << 2) >> 2] | 0;
                            j = (k | 0) == 0 | (k | 0) == (h | 0) ? j : k;
                            if ((h | 0) == 0) {
                                break
                            } else {
                                i = i << 1
                            }
                        }
                    }
                } while (0);
                if ((j | 0) == 0 & (b | 0) == 0) {
                    q = 2 << g;
                    f = f & (q | -q);
                    if ((f | 0) == 0) {
                        break
                    }
                    q = (f & -f) - 1 | 0;
                    n = q >>> 12 & 16;
                    q = q >>> (n >>> 0);
                    m = q >>> 5 & 8;
                    q = q >>> (m >>> 0);
                    o = q >>> 2 & 4;
                    q = q >>> (o >>> 0);
                    p = q >>> 1 & 2;
                    q = q >>> (p >>> 0);
                    j = q >>> 1 & 1;
                    j = c[2856 + ((m | n | o | p | j) + (q >>> (j >>> 0)) << 2) >> 2] | 0
                }
                if ((j | 0) != 0) {
                    while (1) {
                        g = (c[j + 4 >> 2] & -8) - a | 0;
                        f = g >>> 0 < e >>> 0;
                        e = f ? g : e;
                        b = f ? j : b;
                        f = c[j + 16 >> 2] | 0;
                        if ((f | 0) != 0) {
                            j = f;
                            continue
                        }
                        j = c[j + 20 >> 2] | 0;
                        if ((j | 0) == 0) {
                            break
                        }
                    }
                }
                if ((b | 0) == 0) {
                    break
                }
                if (e >>> 0 >= ((c[640] | 0) - a | 0) >>> 0) {
                    break
                }
                d = b;
                i = c[642] | 0;
                if (d >>> 0 < i >>> 0) {
                    ma();
                    return 0
                }
                g = d + a | 0;
                f = g;
                if (d >>> 0 >= g >>> 0) {
                    ma();
                    return 0
                }
                h = c[b + 24 >> 2] | 0;
                j = c[b + 12 >> 2] | 0;
                do {
                    if ((j | 0) == (b | 0)) {
                        k = b + 20 | 0;
                        j = c[k >> 2] | 0;
                        if ((j | 0) == 0) {
                            k = b + 16 | 0;
                            j = c[k >> 2] | 0;
                            if ((j | 0) == 0) {
                                j = 0;
                                break
                            }
                        }
                        while (1) {
                            l = j + 20 | 0;
                            m = c[l >> 2] | 0;
                            if ((m | 0) != 0) {
                                j = m;
                                k = l;
                                continue
                            }
                            l = j + 16 | 0;
                            m = c[l >> 2] | 0;
                            if ((m | 0) == 0) {
                                break
                            } else {
                                j = m;
                                k = l
                            }
                        }
                        if (k >>> 0 < i >>> 0) {
                            ma();
                            return 0
                        } else {
                            c[k >> 2] = 0;
                            break
                        }
                    } else {
                        k = c[b + 8 >> 2] | 0;
                        if (k >>> 0 < i >>> 0) {
                            ma();
                            return 0
                        }
                        i = k + 12 | 0;
                        if ((c[i >> 2] | 0) != (b | 0)) {
                            ma();
                            return 0
                        }
                        l = j + 8 | 0;
                        if ((c[l >> 2] | 0) == (b | 0)) {
                            c[i >> 2] = j;
                            c[l >> 2] = k;
                            break
                        } else {
                            ma();
                            return 0
                        }
                    }
                } while (0);
                c: do {
                    if ((h | 0) != 0) {
                        i = b + 28 | 0;
                        k = 2856 + (c[i >> 2] << 2) | 0;
                        do {
                            if ((b | 0) == (c[k >> 2] | 0)) {
                                c[k >> 2] = j;
                                if ((j | 0) != 0) {
                                    break
                                }
                                c[639] = c[639] & ~(1 << c[i >> 2]);
                                break c
                            } else {
                                if (h >>> 0 < (c[642] | 0) >>> 0) {
                                    ma();
                                    return 0
                                }
                                i = h + 16 | 0;
                                if ((c[i >> 2] | 0) == (b | 0)) {
                                    c[i >> 2] = j
                                } else {
                                    c[h + 20 >> 2] = j
                                }
                                if ((j | 0) == 0) {
                                    break c
                                }
                            }
                        } while (0);
                        if (j >>> 0 < (c[642] | 0) >>> 0) {
                            ma();
                            return 0
                        }
                        c[j + 24 >> 2] = h;
                        h = c[b + 16 >> 2] | 0;
                        do {
                            if ((h | 0) != 0) {
                                if (h >>> 0 < (c[642] | 0) >>> 0) {
                                    ma();
                                    return 0
                                } else {
                                    c[j + 16 >> 2] = h;
                                    c[h + 24 >> 2] = j;
                                    break
                                }
                            }
                        } while (0);
                        h = c[b + 20 >> 2] | 0;
                        if ((h | 0) == 0) {
                            break
                        }
                        if (h >>> 0 < (c[642] | 0) >>> 0) {
                            ma();
                            return 0
                        } else {
                            c[j + 20 >> 2] = h;
                            c[h + 24 >> 2] = j;
                            break
                        }
                    }
                } while (0);
                d: do {
                    if (e >>> 0 < 16 >>> 0) {
                        q = e + a | 0;
                        c[b + 4 >> 2] = q | 3;
                        q = d + (q + 4) | 0;
                        c[q >> 2] = c[q >> 2] | 1
                    } else {
                        c[b + 4 >> 2] = a | 3;
                        c[d + (a | 4) >> 2] = e | 1;
                        c[d + (e + a) >> 2] = e;
                        h = e >>> 3;
                        if (e >>> 0 < 256 >>> 0) {
                            g = h << 1;
                            e = 2592 + (g << 2) | 0;
                            i = c[638] | 0;
                            h = 1 << h;
                            do {
                                if ((i & h | 0) == 0) {
                                    c[638] = i | h;
                                    h = e;
                                    g = 2592 + (g + 2 << 2) | 0
                                } else {
                                    g = 2592 + (g + 2 << 2) | 0;
                                    h = c[g >> 2] | 0;
                                    if (h >>> 0 >= (c[642] | 0) >>> 0) {
                                        break
                                    }
                                    ma();
                                    return 0
                                }
                            } while (0);
                            c[g >> 2] = f;
                            c[h + 12 >> 2] = f;
                            c[d + (a + 8) >> 2] = h;
                            c[d + (a + 12) >> 2] = e;
                            break
                        }
                        f = e >>> 8;
                        do {
                            if ((f | 0) == 0) {
                                h = 0
                            } else {
                                if (e >>> 0 > 16777215 >>> 0) {
                                    h = 31;
                                    break
                                }
                                p = (f + 1048320 | 0) >>> 16 & 8;
                                q = f << p;
                                o = (q + 520192 | 0) >>> 16 & 4;
                                q = q << o;
                                h = (q + 245760 | 0) >>> 16 & 2;
                                h = 14 - (o | p | h) + (q << h >>> 15) | 0;
                                h = e >>> ((h + 7 | 0) >>> 0) & 1 | h << 1
                            }
                        } while (0);
                        f = 2856 + (h << 2) | 0;
                        c[d + (a + 28) >> 2] = h;
                        c[d + (a + 20) >> 2] = 0;
                        c[d + (a + 16) >> 2] = 0;
                        j = c[639] | 0;
                        i = 1 << h;
                        if ((j & i | 0) == 0) {
                            c[639] = j | i;
                            c[f >> 2] = g;
                            c[d + (a + 24) >> 2] = f;
                            c[d + (a + 12) >> 2] = g;
                            c[d + (a + 8) >> 2] = g;
                            break
                        }
                        f = c[f >> 2] | 0;
                        if ((h | 0) == 31) {
                            h = 0
                        } else {
                            h = 25 - (h >>> 1) | 0
                        }
                        e: do {
                            if ((c[f + 4 >> 2] & -8 | 0) != (e | 0)) {
                                h = e << h;
                                while (1) {
                                    i = f + 16 + (h >>> 31 << 2) | 0;
                                    j = c[i >> 2] | 0;
                                    if ((j | 0) == 0) {
                                        break
                                    }
                                    if ((c[j + 4 >> 2] & -8 | 0) == (e | 0)) {
                                        f = j;
                                        break e
                                    } else {
                                        f = j;
                                        h = h << 1
                                    }
                                }
                                if (i >>> 0 < (c[642] | 0) >>> 0) {
                                    ma();
                                    return 0
                                } else {
                                    c[i >> 2] = g;
                                    c[d + (a + 24) >> 2] = f;
                                    c[d + (a + 12) >> 2] = g;
                                    c[d + (a + 8) >> 2] = g;
                                    break d
                                }
                            }
                        } while (0);
                        h = f + 8 | 0;
                        e = c[h >> 2] | 0;
                        q = c[642] | 0;
                        if (f >>> 0 >= q >>> 0 & e >>> 0 >= q >>> 0) {
                            c[e + 12 >> 2] = g;
                            c[h >> 2] = g;
                            c[d + (a + 8) >> 2] = e;
                            c[d + (a + 12) >> 2] = f;
                            c[d + (a + 24) >> 2] = 0;
                            break
                        } else {
                            ma();
                            return 0
                        }
                    }
                } while (0);
                q = b + 8 | 0;
                return q | 0
            }
        } while (0);
        b = c[640] | 0;
        if (b >>> 0 >= a >>> 0) {
            d = b - a | 0;
            e = c[643] | 0;
            if (d >>> 0 > 15 >>> 0) {
                q = e;
                c[643] = q + a;
                c[640] = d;
                c[q + (a + 4) >> 2] = d | 1;
                c[q + b >> 2] = d;
                c[e + 4 >> 2] = a | 3
            } else {
                c[640] = 0;
                c[643] = 0;
                c[e + 4 >> 2] = b | 3;
                q = e + (b + 4) | 0;
                c[q >> 2] = c[q >> 2] | 1
            }
            q = e + 8 | 0;
            return q | 0
        }
        b = c[641] | 0;
        if (b >>> 0 > a >>> 0) {
            o = b - a | 0;
            c[641] = o;
            q = c[644] | 0;
            p = q;
            c[644] = p + a;
            c[p + (a + 4) >> 2] = o | 1;
            c[q + 4 >> 2] = a | 3;
            q = q + 8 | 0;
            return q | 0
        }
        do {
            if ((c[632] | 0) == 0) {
                b = la(30) | 0;
                if ((b - 1 & b | 0) == 0) {
                    c[634] = b;
                    c[633] = b;
                    c[635] = -1;
                    c[636] = -1;
                    c[637] = 0;
                    c[749] = 0;
                    c[632] = (Ja(0) | 0) & -16 ^ 1431655768;
                    break
                } else {
                    ma();
                    return 0
                }
            }
        } while (0);
        h = a + 48 | 0;
        e = c[634] | 0;
        g = a + 47 | 0;
        b = e + g | 0;
        e = -e | 0;
        f = b & e;
        if (f >>> 0 <= a >>> 0) {
            q = 0;
            return q | 0
        }
        i = c[748] | 0;
        do {
            if ((i | 0) != 0) {
                p = c[746] | 0;
                q = p + f | 0;
                if (q >>> 0 <= p >>> 0 | q >>> 0 > i >>> 0) {
                    a = 0
                } else {
                    break
                }
                return a | 0
            }
        } while (0);
        f: do {
            if ((c[749] & 4 | 0) == 0) {
                k = c[644] | 0;
                g: do {
                    if ((k | 0) == 0) {
                        d = 181
                    } else {
                        l = 3e3;
                        while (1) {
                            j = l | 0;
                            m = c[j >> 2] | 0;
                            if (m >>> 0 <= k >>> 0) {
                                i = l + 4 | 0;
                                if ((m + (c[i >> 2] | 0) | 0) >>> 0 > k >>> 0) {
                                    break
                                }
                            }
                            l = c[l + 8 >> 2] | 0;
                            if ((l | 0) == 0) {
                                d = 181;
                                break g
                            }
                        }
                        if ((l | 0) == 0) {
                            d = 181;
                            break
                        }
                        e = b - (c[641] | 0) & e;
                        if (e >>> 0 >= 2147483647 >>> 0) {
                            e = 0;
                            break
                        }
                        b = Ga(e | 0) | 0;
                        if ((b | 0) == ((c[j >> 2] | 0) + (c[i >> 2] | 0) | 0)) {
                            d = 190
                        } else {
                            d = 191
                        }
                    }
                } while (0);
                do {
                    if ((d | 0) == 181) {
                        i = Ga(0) | 0;
                        if ((i | 0) == -1) {
                            e = 0;
                            break
                        }
                        e = i;
                        b = c[633] | 0;
                        j = b - 1 | 0;
                        if ((j & e | 0) == 0) {
                            e = f
                        } else {
                            e = f - e + (j + e & -b) | 0
                        }
                        j = c[746] | 0;
                        b = j + e | 0;
                        if (!(e >>> 0 > a >>> 0 & e >>> 0 < 2147483647 >>> 0)) {
                            e = 0;
                            break
                        }
                        k = c[748] | 0;
                        if ((k | 0) != 0) {
                            if (b >>> 0 <= j >>> 0 | b >>> 0 > k >>> 0) {
                                e = 0;
                                break
                            }
                        }
                        b = Ga(e | 0) | 0;
                        if ((b | 0) == (i | 0)) {
                            b = i;
                            d = 190
                        } else {
                            d = 191
                        }
                    }
                } while (0);
                h: do {
                    if ((d | 0) == 190) {
                        if ((b | 0) != -1) {
                            d = 201;
                            break f
                        }
                    } else if ((d | 0) == 191) {
                        d = -e | 0;
                        do {
                            if ((b | 0) != -1 & e >>> 0 < 2147483647 >>> 0 & h >>> 0 > e >>> 0) {
                                q = c[634] | 0;
                                g = g - e + q & -q;
                                if (g >>> 0 >= 2147483647 >>> 0) {
                                    break
                                }
                                if ((Ga(g | 0) | 0) == -1) {
                                    Ga(d | 0) | 0;
                                    e = 0;
                                    break h
                                } else {
                                    e = g + e | 0;
                                    break
                                }
                            }
                        } while (0);
                        if ((b | 0) == -1) {
                            e = 0
                        } else {
                            d = 201;
                            break f
                        }
                    }
                } while (0);
                c[749] = c[749] | 4;
                d = 198
            } else {
                e = 0;
                d = 198
            }
        } while (0);
        do {
            if ((d | 0) == 198) {
                if (f >>> 0 >= 2147483647 >>> 0) {
                    break
                }
                b = Ga(f | 0) | 0;
                f = Ga(0) | 0;
                if (!((b | 0) != -1 & (f | 0) != -1 & b >>> 0 < f >>> 0)) {
                    break
                }
                g = f - b | 0;
                f = g >>> 0 > (a + 40 | 0) >>> 0;
                if (f) {
                    e = f ? g : e;
                    d = 201
                }
            }
        } while (0);
        do {
            if ((d | 0) == 201) {
                f = (c[746] | 0) + e | 0;
                c[746] = f;
                if (f >>> 0 > (c[747] | 0) >>> 0) {
                    c[747] = f
                }
                f = c[644] | 0;
                i: do {
                    if ((f | 0) == 0) {
                        q = c[642] | 0;
                        if ((q | 0) == 0 | b >>> 0 < q >>> 0) {
                            c[642] = b
                        }
                        c[750] = b;
                        c[751] = e;
                        c[753] = 0;
                        c[647] = c[632];
                        c[646] = -1;
                        d = 0;
                        do {
                            q = d << 1;
                            p = 2592 + (q << 2) | 0;
                            c[2592 + (q + 3 << 2) >> 2] = p;
                            c[2592 + (q + 2 << 2) >> 2] = p;
                            d = d + 1 | 0;
                        } while (d >>> 0 < 32 >>> 0);
                        d = b + 8 | 0;
                        if ((d & 7 | 0) == 0) {
                            d = 0
                        } else {
                            d = -d & 7
                        }
                        q = e - 40 - d | 0;
                        c[644] = b + d;
                        c[641] = q;
                        c[b + (d + 4) >> 2] = q | 1;
                        c[b + (e - 36) >> 2] = 40;
                        c[645] = c[636]
                    } else {
                        g = 3e3;
                        do {
                            j = c[g >> 2] | 0;
                            i = g + 4 | 0;
                            h = c[i >> 2] | 0;
                            if ((b | 0) == (j + h | 0)) {
                                d = 213;
                                break
                            }
                            g = c[g + 8 >> 2] | 0;
                        } while ((g | 0) != 0);
                        do {
                            if ((d | 0) == 213) {
                                if ((c[g + 12 >> 2] & 8 | 0) != 0) {
                                    break
                                }
                                q = f;
                                if (!(q >>> 0 >= j >>> 0 & q >>> 0 < b >>> 0)) {
                                    break
                                }
                                c[i >> 2] = h + e;
                                q = c[644] | 0;
                                b = (c[641] | 0) + e | 0;
                                d = q;
                                e = q + 8 | 0;
                                if ((e & 7 | 0) == 0) {
                                    e = 0
                                } else {
                                    e = -e & 7
                                }
                                q = b - e | 0;
                                c[644] = d + e;
                                c[641] = q;
                                c[d + (e + 4) >> 2] = q | 1;
                                c[d + (b + 4) >> 2] = 40;
                                c[645] = c[636];
                                break i
                            }
                        } while (0);
                        if (b >>> 0 < (c[642] | 0) >>> 0) {
                            c[642] = b
                        }
                        g = b + e | 0;
                        i = 3e3;
                        do {
                            h = i | 0;
                            if ((c[h >> 2] | 0) == (g | 0)) {
                                d = 223;
                                break
                            }
                            i = c[i + 8 >> 2] | 0;
                        } while ((i | 0) != 0);
                        do {
                            if ((d | 0) == 223) {
                                if ((c[i + 12 >> 2] & 8 | 0) != 0) {
                                    break
                                }
                                c[h >> 2] = b;
                                d = i + 4 | 0;
                                c[d >> 2] = (c[d >> 2] | 0) + e;
                                d = b + 8 | 0;
                                if ((d & 7 | 0) == 0) {
                                    d = 0
                                } else {
                                    d = -d & 7
                                }
                                f = b + (e + 8) | 0;
                                if ((f & 7 | 0) == 0) {
                                    j = 0
                                } else {
                                    j = -f & 7
                                }
                                m = b + (j + e) | 0;
                                l = m;
                                f = d + a | 0;
                                h = b + f | 0;
                                g = h;
                                i = m - (b + d) - a | 0;
                                c[b + (d + 4) >> 2] = a | 3;
                                j: do {
                                    if ((l | 0) == (c[644] | 0)) {
                                        q = (c[641] | 0) + i | 0;
                                        c[641] = q;
                                        c[644] = g;
                                        c[b + (f + 4) >> 2] = q | 1
                                    } else {
                                        if ((l | 0) == (c[643] | 0)) {
                                            q = (c[640] | 0) + i | 0;
                                            c[640] = q;
                                            c[643] = g;
                                            c[b + (f + 4) >> 2] = q | 1;
                                            c[b + (q + f) >> 2] = q;
                                            break
                                        }
                                        k = e + 4 | 0;
                                        o = c[b + (k + j) >> 2] | 0;
                                        if ((o & 3 | 0) == 1) {
                                            a = o & -8;
                                            n = o >>> 3;
                                            k: do {
                                                if (o >>> 0 < 256 >>> 0) {
                                                    k = c[b + ((j | 8) + e) >> 2] | 0;
                                                    m = c[b + (e + 12 + j) >> 2] | 0;
                                                    o = 2592 + (n << 1 << 2) | 0;
                                                    do {
                                                        if ((k | 0) != (o | 0)) {
                                                            if (k >>> 0 < (c[642] | 0) >>> 0) {
                                                                ma();
                                                                return 0
                                                            }
                                                            if ((c[k + 12 >> 2] | 0) == (l | 0)) {
                                                                break
                                                            }
                                                            ma();
                                                            return 0
                                                        }
                                                    } while (0);
                                                    if ((m | 0) == (k | 0)) {
                                                        c[638] = c[638] & ~(1 << n);
                                                        break
                                                    }
                                                    do {
                                                        if ((m | 0) == (o | 0)) {
                                                            n = m + 8 | 0
                                                        } else {
                                                            if (m >>> 0 < (c[642] | 0) >>> 0) {
                                                                ma();
                                                                return 0
                                                            }
                                                            n = m + 8 | 0;
                                                            if ((c[n >> 2] | 0) == (l | 0)) {
                                                                break
                                                            }
                                                            ma();
                                                            return 0
                                                        }
                                                    } while (0);
                                                    c[k + 12 >> 2] = m;
                                                    c[n >> 2] = k
                                                } else {
                                                    l = c[b + ((j | 24) + e) >> 2] | 0;
                                                    n = c[b + (e + 12 + j) >> 2] | 0;
                                                    do {
                                                        if ((n | 0) == (m | 0)) {
                                                            p = j | 16;
                                                            o = b + (k + p) | 0;
                                                            n = c[o >> 2] | 0;
                                                            if ((n | 0) == 0) {
                                                                o = b + (p + e) | 0;
                                                                n = c[o >> 2] | 0;
                                                                if ((n | 0) == 0) {
                                                                    n = 0;
                                                                    break
                                                                }
                                                            }
                                                            while (1) {
                                                                q = n + 20 | 0;
                                                                p = c[q >> 2] | 0;
                                                                if ((p | 0) != 0) {
                                                                    n = p;
                                                                    o = q;
                                                                    continue
                                                                }
                                                                p = n + 16 | 0;
                                                                q = c[p >> 2] | 0;
                                                                if ((q | 0) == 0) {
                                                                    break
                                                                } else {
                                                                    n = q;
                                                                    o = p
                                                                }
                                                            }
                                                            if (o >>> 0 < (c[642] | 0) >>> 0) {
                                                                ma();
                                                                return 0
                                                            } else {
                                                                c[o >> 2] = 0;
                                                                break
                                                            }
                                                        } else {
                                                            q = c[b + ((j | 8) + e) >> 2] | 0;
                                                            if (q >>> 0 < (c[642] | 0) >>> 0) {
                                                                ma();
                                                                return 0
                                                            }
                                                            o = q + 12 | 0;
                                                            if ((c[o >> 2] | 0) != (m | 0)) {
                                                                ma();
                                                                return 0
                                                            }
                                                            p = n + 8 | 0;
                                                            if ((c[p >> 2] | 0) == (m | 0)) {
                                                                c[o >> 2] = n;
                                                                c[p >> 2] = q;
                                                                break
                                                            } else {
                                                                ma();
                                                                return 0
                                                            }
                                                        }
                                                    } while (0);
                                                    if ((l | 0) == 0) {
                                                        break
                                                    }
                                                    o = b + (e + 28 + j) | 0;
                                                    p = 2856 + (c[o >> 2] << 2) | 0;
                                                    do {
                                                        if ((m | 0) == (c[p >> 2] | 0)) {
                                                            c[p >> 2] = n;
                                                            if ((n | 0) != 0) {
                                                                break
                                                            }
                                                            c[639] = c[639] & ~(1 << c[o >> 2]);
                                                            break k
                                                        } else {
                                                            if (l >>> 0 < (c[642] | 0) >>> 0) {
                                                                ma();
                                                                return 0
                                                            }
                                                            o = l + 16 | 0;
                                                            if ((c[o >> 2] | 0) == (m | 0)) {
                                                                c[o >> 2] = n
                                                            } else {
                                                                c[l + 20 >> 2] = n
                                                            }
                                                            if ((n | 0) == 0) {
                                                                break k
                                                            }
                                                        }
                                                    } while (0);
                                                    if (n >>> 0 < (c[642] | 0) >>> 0) {
                                                        ma();
                                                        return 0
                                                    }
                                                    c[n + 24 >> 2] = l;
                                                    m = j | 16;
                                                    l = c[b + (m + e) >> 2] | 0;
                                                    do {
                                                        if ((l | 0) != 0) {
                                                            if (l >>> 0 < (c[642] | 0) >>> 0) {
                                                                ma();
                                                                return 0
                                                            } else {
                                                                c[n + 16 >> 2] = l;
                                                                c[l + 24 >> 2] = n;
                                                                break
                                                            }
                                                        }
                                                    } while (0);
                                                    k = c[b + (k + m) >> 2] | 0;
                                                    if ((k | 0) == 0) {
                                                        break
                                                    }
                                                    if (k >>> 0 < (c[642] | 0) >>> 0) {
                                                        ma();
                                                        return 0
                                                    } else {
                                                        c[n + 20 >> 2] = k;
                                                        c[k + 24 >> 2] = n;
                                                        break
                                                    }
                                                }
                                            } while (0);
                                            l = b + ((a | j) + e) | 0;
                                            i = a + i | 0
                                        }
                                        e = l + 4 | 0;
                                        c[e >> 2] = c[e >> 2] & -2;
                                        c[b + (f + 4) >> 2] = i | 1;
                                        c[b + (i + f) >> 2] = i;
                                        e = i >>> 3;
                                        if (i >>> 0 < 256 >>> 0) {
                                            h = e << 1;
                                            a = 2592 + (h << 2) | 0;
                                            i = c[638] | 0;
                                            e = 1 << e;
                                            do {
                                                if ((i & e | 0) == 0) {
                                                    c[638] = i | e;
                                                    e = a;
                                                    h = 2592 + (h + 2 << 2) | 0
                                                } else {
                                                    h = 2592 + (h + 2 << 2) | 0;
                                                    e = c[h >> 2] | 0;
                                                    if (e >>> 0 >= (c[642] | 0) >>> 0) {
                                                        break
                                                    }
                                                    ma();
                                                    return 0
                                                }
                                            } while (0);
                                            c[h >> 2] = g;
                                            c[e + 12 >> 2] = g;
                                            c[b + (f + 8) >> 2] = e;
                                            c[b + (f + 12) >> 2] = a;
                                            break
                                        }
                                        a = i >>> 8;
                                        do {
                                            if ((a | 0) == 0) {
                                                e = 0
                                            } else {
                                                if (i >>> 0 > 16777215 >>> 0) {
                                                    e = 31;
                                                    break
                                                }
                                                p = (a + 1048320 | 0) >>> 16 & 8;
                                                q = a << p;
                                                o = (q + 520192 | 0) >>> 16 & 4;
                                                q = q << o;
                                                e = (q + 245760 | 0) >>> 16 & 2;
                                                e = 14 - (o | p | e) + (q << e >>> 15) | 0;
                                                e = i >>> ((e + 7 | 0) >>> 0) & 1 | e << 1
                                            }
                                        } while (0);
                                        a = 2856 + (e << 2) | 0;
                                        c[b + (f + 28) >> 2] = e;
                                        c[b + (f + 20) >> 2] = 0;
                                        c[b + (f + 16) >> 2] = 0;
                                        j = c[639] | 0;
                                        g = 1 << e;
                                        if ((j & g | 0) == 0) {
                                            c[639] = j | g;
                                            c[a >> 2] = h;
                                            c[b + (f + 24) >> 2] = a;
                                            c[b + (f + 12) >> 2] = h;
                                            c[b + (f + 8) >> 2] = h;
                                            break
                                        }
                                        a = c[a >> 2] | 0;
                                        if ((e | 0) == 31) {
                                            e = 0
                                        } else {
                                            e = 25 - (e >>> 1) | 0
                                        }
                                        l: do {
                                            if ((c[a + 4 >> 2] & -8 | 0) != (i | 0)) {
                                                j = i << e;
                                                while (1) {
                                                    g = a + 16 + (j >>> 31 << 2) | 0;
                                                    e = c[g >> 2] | 0;
                                                    if ((e | 0) == 0) {
                                                        break
                                                    }
                                                    if ((c[e + 4 >> 2] & -8 | 0) == (i | 0)) {
                                                        a = e;
                                                        break l
                                                    } else {
                                                        a = e;
                                                        j = j << 1
                                                    }
                                                }
                                                if (g >>> 0 < (c[642] | 0) >>> 0) {
                                                    ma();
                                                    return 0
                                                } else {
                                                    c[g >> 2] = h;
                                                    c[b + (f + 24) >> 2] = a;
                                                    c[b + (f + 12) >> 2] = h;
                                                    c[b + (f + 8) >> 2] = h;
                                                    break j
                                                }
                                            }
                                        } while (0);
                                        e = a + 8 | 0;
                                        g = c[e >> 2] | 0;
                                        q = c[642] | 0;
                                        if (a >>> 0 >= q >>> 0 & g >>> 0 >= q >>> 0) {
                                            c[g + 12 >> 2] = h;
                                            c[e >> 2] = h;
                                            c[b + (f + 8) >> 2] = g;
                                            c[b + (f + 12) >> 2] = a;
                                            c[b + (f + 24) >> 2] = 0;
                                            break
                                        } else {
                                            ma();
                                            return 0
                                        }
                                    }
                                } while (0);
                                q = b + (d | 8) | 0;
                                return q | 0
                            }
                        } while (0);
                        d = f;
                        j = 3e3;
                        while (1) {
                            i = c[j >> 2] | 0;
                            if (i >>> 0 <= d >>> 0) {
                                h = c[j + 4 >> 2] | 0;
                                g = i + h | 0;
                                if (g >>> 0 > d >>> 0) {
                                    break
                                }
                            }
                            j = c[j + 8 >> 2] | 0
                        }
                        j = i + (h - 39) | 0;
                        if ((j & 7 | 0) == 0) {
                            j = 0
                        } else {
                            j = -j & 7
                        }
                        h = i + (h - 47 + j) | 0;
                        h = h >>> 0 < (f + 16 | 0) >>> 0 ? d : h;
                        i = h + 8 | 0;
                        j = b + 8 | 0;
                        if ((j & 7 | 0) == 0) {
                            j = 0
                        } else {
                            j = -j & 7
                        }
                        q = e - 40 - j | 0;
                        c[644] = b + j;
                        c[641] = q;
                        c[b + (j + 4) >> 2] = q | 1;
                        c[b + (e - 36) >> 2] = 40;
                        c[645] = c[636];
                        c[h + 4 >> 2] = 27;
                        c[i >> 2] = c[750];
                        c[i + 4 >> 2] = c[751];
                        c[i + 8 >> 2] = c[752];
                        c[i + 12 >> 2] = c[753];
                        c[750] = b;
                        c[751] = e;
                        c[753] = 0;
                        c[752] = i;
                        e = h + 28 | 0;
                        c[e >> 2] = 7;
                        if ((h + 32 | 0) >>> 0 < g >>> 0) {
                            while (1) {
                                b = e + 4 | 0;
                                c[b >> 2] = 7;
                                if ((e + 8 | 0) >>> 0 < g >>> 0) {
                                    e = b
                                } else {
                                    break
                                }
                            }
                        }
                        if ((h | 0) == (d | 0)) {
                            break
                        }
                        e = h - f | 0;
                        g = d + (e + 4) | 0;
                        c[g >> 2] = c[g >> 2] & -2;
                        c[f + 4 >> 2] = e | 1;
                        c[d + e >> 2] = e;
                        g = e >>> 3;
                        if (e >>> 0 < 256 >>> 0) {
                            d = g << 1;
                            b = 2592 + (d << 2) | 0;
                            e = c[638] | 0;
                            g = 1 << g;
                            do {
                                if ((e & g | 0) == 0) {
                                    c[638] = e | g;
                                    e = b;
                                    d = 2592 + (d + 2 << 2) | 0
                                } else {
                                    d = 2592 + (d + 2 << 2) | 0;
                                    e = c[d >> 2] | 0;
                                    if (e >>> 0 >= (c[642] | 0) >>> 0) {
                                        break
                                    }
                                    ma();
                                    return 0
                                }
                            } while (0);
                            c[d >> 2] = f;
                            c[e + 12 >> 2] = f;
                            c[f + 8 >> 2] = e;
                            c[f + 12 >> 2] = b;
                            break
                        }
                        b = f;
                        d = e >>> 8;
                        do {
                            if ((d | 0) == 0) {
                                d = 0
                            } else {
                                if (e >>> 0 > 16777215 >>> 0) {
                                    d = 31;
                                    break
                                }
                                p = (d + 1048320 | 0) >>> 16 & 8;
                                q = d << p;
                                o = (q + 520192 | 0) >>> 16 & 4;
                                q = q << o;
                                d = (q + 245760 | 0) >>> 16 & 2;
                                d = 14 - (o | p | d) + (q << d >>> 15) | 0;
                                d = e >>> ((d + 7 | 0) >>> 0) & 1 | d << 1
                            }
                        } while (0);
                        g = 2856 + (d << 2) | 0;
                        c[f + 28 >> 2] = d;
                        c[f + 20 >> 2] = 0;
                        c[f + 16 >> 2] = 0;
                        i = c[639] | 0;
                        h = 1 << d;
                        if ((i & h | 0) == 0) {
                            c[639] = i | h;
                            c[g >> 2] = b;
                            c[f + 24 >> 2] = g;
                            c[f + 12 >> 2] = f;
                            c[f + 8 >> 2] = f;
                            break
                        }
                        i = c[g >> 2] | 0;
                        if ((d | 0) == 31) {
                            g = 0
                        } else {
                            g = 25 - (d >>> 1) | 0
                        }
                        m: do {
                            if ((c[i + 4 >> 2] & -8 | 0) != (e | 0)) {
                                d = i;
                                h = e << g;
                                while (1) {
                                    g = d + 16 + (h >>> 31 << 2) | 0;
                                    i = c[g >> 2] | 0;
                                    if ((i | 0) == 0) {
                                        break
                                    }
                                    if ((c[i + 4 >> 2] & -8 | 0) == (e | 0)) {
                                        break m
                                    } else {
                                        d = i;
                                        h = h << 1
                                    }
                                }
                                if (g >>> 0 < (c[642] | 0) >>> 0) {
                                    ma();
                                    return 0
                                } else {
                                    c[g >> 2] = b;
                                    c[f + 24 >> 2] = d;
                                    c[f + 12 >> 2] = f;
                                    c[f + 8 >> 2] = f;
                                    break i
                                }
                            }
                        } while (0);
                        d = i + 8 | 0;
                        e = c[d >> 2] | 0;
                        q = c[642] | 0;
                        if (i >>> 0 >= q >>> 0 & e >>> 0 >= q >>> 0) {
                            c[e + 12 >> 2] = b;
                            c[d >> 2] = b;
                            c[f + 8 >> 2] = e;
                            c[f + 12 >> 2] = i;
                            c[f + 24 >> 2] = 0;
                            break
                        } else {
                            ma();
                            return 0
                        }
                    }
                } while (0);
                b = c[641] | 0;
                if (b >>> 0 <= a >>> 0) {
                    break
                }
                o = b - a | 0;
                c[641] = o;
                q = c[644] | 0;
                p = q;
                c[644] = p + a;
                c[p + (a + 4) >> 2] = o | 1;
                c[q + 4 >> 2] = a | 3;
                q = q + 8 | 0;
                return q | 0
            }
        } while (0);
        c[(Ha() | 0) >> 2] = 12;
        q = 0;
        return q | 0
    }

    function cc(a) {
        a = a | 0;
        var b = 0,
            d = 0,
            e = 0,
            f = 0,
            g = 0,
            h = 0,
            i = 0,
            j = 0,
            k = 0,
            l = 0,
            m = 0,
            n = 0,
            o = 0,
            p = 0,
            q = 0,
            r = 0,
            s = 0,
            t = 0,
            u = 0,
            v = 0,
            w = 0;
        if ((a | 0) == 0) {
            return
        }
        p = a - 8 | 0;
        r = p;
        q = c[642] | 0;
        if (p >>> 0 < q >>> 0) {
            ma()
        }
        n = c[a - 4 >> 2] | 0;
        m = n & 3;
        if ((m | 0) == 1) {
            ma()
        }
        h = n & -8;
        k = a + (h - 8) | 0;
        i = k;
        a: do {
            if ((n & 1 | 0) == 0) {
                u = c[p >> 2] | 0;
                if ((m | 0) == 0) {
                    return
                }
                p = -8 - u | 0;
                r = a + p | 0;
                m = r;
                n = u + h | 0;
                if (r >>> 0 < q >>> 0) {
                    ma()
                }
                if ((m | 0) == (c[643] | 0)) {
                    b = a + (h - 4) | 0;
                    if ((c[b >> 2] & 3 | 0) != 3) {
                        b = m;
                        l = n;
                        break
                    }
                    c[640] = n;
                    c[b >> 2] = c[b >> 2] & -2;
                    c[a + (p + 4) >> 2] = n | 1;
                    c[k >> 2] = n;
                    return
                }
                t = u >>> 3;
                if (u >>> 0 < 256 >>> 0) {
                    b = c[a + (p + 8) >> 2] | 0;
                    l = c[a + (p + 12) >> 2] | 0;
                    o = 2592 + (t << 1 << 2) | 0;
                    do {
                        if ((b | 0) != (o | 0)) {
                            if (b >>> 0 < q >>> 0) {
                                ma()
                            }
                            if ((c[b + 12 >> 2] | 0) == (m | 0)) {
                                break
                            }
                            ma()
                        }
                    } while (0);
                    if ((l | 0) == (b | 0)) {
                        c[638] = c[638] & ~(1 << t);
                        b = m;
                        l = n;
                        break
                    }
                    do {
                        if ((l | 0) == (o | 0)) {
                            s = l + 8 | 0
                        } else {
                            if (l >>> 0 < q >>> 0) {
                                ma()
                            }
                            o = l + 8 | 0;
                            if ((c[o >> 2] | 0) == (m | 0)) {
                                s = o;
                                break
                            }
                            ma()
                        }
                    } while (0);
                    c[b + 12 >> 2] = l;
                    c[s >> 2] = b;
                    b = m;
                    l = n;
                    break
                }
                s = c[a + (p + 24) >> 2] | 0;
                u = c[a + (p + 12) >> 2] | 0;
                do {
                    if ((u | 0) == (r | 0)) {
                        u = a + (p + 20) | 0;
                        t = c[u >> 2] | 0;
                        if ((t | 0) == 0) {
                            u = a + (p + 16) | 0;
                            t = c[u >> 2] | 0;
                            if ((t | 0) == 0) {
                                o = 0;
                                break
                            }
                        }
                        while (1) {
                            w = t + 20 | 0;
                            v = c[w >> 2] | 0;
                            if ((v | 0) != 0) {
                                t = v;
                                u = w;
                                continue
                            }
                            v = t + 16 | 0;
                            w = c[v >> 2] | 0;
                            if ((w | 0) == 0) {
                                break
                            } else {
                                t = w;
                                u = v
                            }
                        }
                        if (u >>> 0 < q >>> 0) {
                            ma()
                        } else {
                            c[u >> 2] = 0;
                            o = t;
                            break
                        }
                    } else {
                        t = c[a + (p + 8) >> 2] | 0;
                        if (t >>> 0 < q >>> 0) {
                            ma()
                        }
                        q = t + 12 | 0;
                        if ((c[q >> 2] | 0) != (r | 0)) {
                            ma()
                        }
                        v = u + 8 | 0;
                        if ((c[v >> 2] | 0) == (r | 0)) {
                            c[q >> 2] = u;
                            c[v >> 2] = t;
                            o = u;
                            break
                        } else {
                            ma()
                        }
                    }
                } while (0);
                if ((s | 0) == 0) {
                    b = m;
                    l = n;
                    break
                }
                q = a + (p + 28) | 0;
                t = 2856 + (c[q >> 2] << 2) | 0;
                do {
                    if ((r | 0) == (c[t >> 2] | 0)) {
                        c[t >> 2] = o;
                        if ((o | 0) != 0) {
                            break
                        }
                        c[639] = c[639] & ~(1 << c[q >> 2]);
                        b = m;
                        l = n;
                        break a
                    } else {
                        if (s >>> 0 < (c[642] | 0) >>> 0) {
                            ma()
                        }
                        q = s + 16 | 0;
                        if ((c[q >> 2] | 0) == (r | 0)) {
                            c[q >> 2] = o
                        } else {
                            c[s + 20 >> 2] = o
                        }
                        if ((o | 0) == 0) {
                            b = m;
                            l = n;
                            break a
                        }
                    }
                } while (0);
                if (o >>> 0 < (c[642] | 0) >>> 0) {
                    ma()
                }
                c[o + 24 >> 2] = s;
                q = c[a + (p + 16) >> 2] | 0;
                do {
                    if ((q | 0) != 0) {
                        if (q >>> 0 < (c[642] | 0) >>> 0) {
                            ma()
                        } else {
                            c[o + 16 >> 2] = q;
                            c[q + 24 >> 2] = o;
                            break
                        }
                    }
                } while (0);
                p = c[a + (p + 20) >> 2] | 0;
                if ((p | 0) == 0) {
                    b = m;
                    l = n;
                    break
                }
                if (p >>> 0 < (c[642] | 0) >>> 0) {
                    ma()
                } else {
                    c[o + 20 >> 2] = p;
                    c[p + 24 >> 2] = o;
                    b = m;
                    l = n;
                    break
                }
            } else {
                b = r;
                l = h
            }
        } while (0);
        m = b;
        if (m >>> 0 >= k >>> 0) {
            ma()
        }
        n = a + (h - 4) | 0;
        o = c[n >> 2] | 0;
        if ((o & 1 | 0) == 0) {
            ma()
        }
        do {
            if ((o & 2 | 0) == 0) {
                if ((i | 0) == (c[644] | 0)) {
                    w = (c[641] | 0) + l | 0;
                    c[641] = w;
                    c[644] = b;
                    c[b + 4 >> 2] = w | 1;
                    if ((b | 0) != (c[643] | 0)) {
                        return
                    }
                    c[643] = 0;
                    c[640] = 0;
                    return
                }
                if ((i | 0) == (c[643] | 0)) {
                    w = (c[640] | 0) + l | 0;
                    c[640] = w;
                    c[643] = b;
                    c[b + 4 >> 2] = w | 1;
                    c[m + w >> 2] = w;
                    return
                }
                l = (o & -8) + l | 0;
                n = o >>> 3;
                b: do {
                    if (o >>> 0 < 256 >>> 0) {
                        g = c[a + h >> 2] | 0;
                        h = c[a + (h | 4) >> 2] | 0;
                        a = 2592 + (n << 1 << 2) | 0;
                        do {
                            if ((g | 0) != (a | 0)) {
                                if (g >>> 0 < (c[642] | 0) >>> 0) {
                                    ma()
                                }
                                if ((c[g + 12 >> 2] | 0) == (i | 0)) {
                                    break
                                }
                                ma()
                            }
                        } while (0);
                        if ((h | 0) == (g | 0)) {
                            c[638] = c[638] & ~(1 << n);
                            break
                        }
                        do {
                            if ((h | 0) == (a | 0)) {
                                j = h + 8 | 0
                            } else {
                                if (h >>> 0 < (c[642] | 0) >>> 0) {
                                    ma()
                                }
                                a = h + 8 | 0;
                                if ((c[a >> 2] | 0) == (i | 0)) {
                                    j = a;
                                    break
                                }
                                ma()
                            }
                        } while (0);
                        c[g + 12 >> 2] = h;
                        c[j >> 2] = g
                    } else {
                        i = c[a + (h + 16) >> 2] | 0;
                        n = c[a + (h | 4) >> 2] | 0;
                        do {
                            if ((n | 0) == (k | 0)) {
                                n = a + (h + 12) | 0;
                                j = c[n >> 2] | 0;
                                if ((j | 0) == 0) {
                                    n = a + (h + 8) | 0;
                                    j = c[n >> 2] | 0;
                                    if ((j | 0) == 0) {
                                        g = 0;
                                        break
                                    }
                                }
                                while (1) {
                                    p = j + 20 | 0;
                                    o = c[p >> 2] | 0;
                                    if ((o | 0) != 0) {
                                        j = o;
                                        n = p;
                                        continue
                                    }
                                    o = j + 16 | 0;
                                    p = c[o >> 2] | 0;
                                    if ((p | 0) == 0) {
                                        break
                                    } else {
                                        j = p;
                                        n = o
                                    }
                                }
                                if (n >>> 0 < (c[642] | 0) >>> 0) {
                                    ma()
                                } else {
                                    c[n >> 2] = 0;
                                    g = j;
                                    break
                                }
                            } else {
                                o = c[a + h >> 2] | 0;
                                if (o >>> 0 < (c[642] | 0) >>> 0) {
                                    ma()
                                }
                                p = o + 12 | 0;
                                if ((c[p >> 2] | 0) != (k | 0)) {
                                    ma()
                                }
                                j = n + 8 | 0;
                                if ((c[j >> 2] | 0) == (k | 0)) {
                                    c[p >> 2] = n;
                                    c[j >> 2] = o;
                                    g = n;
                                    break
                                } else {
                                    ma()
                                }
                            }
                        } while (0);
                        if ((i | 0) == 0) {
                            break
                        }
                        j = a + (h + 20) | 0;
                        n = 2856 + (c[j >> 2] << 2) | 0;
                        do {
                            if ((k | 0) == (c[n >> 2] | 0)) {
                                c[n >> 2] = g;
                                if ((g | 0) != 0) {
                                    break
                                }
                                c[639] = c[639] & ~(1 << c[j >> 2]);
                                break b
                            } else {
                                if (i >>> 0 < (c[642] | 0) >>> 0) {
                                    ma()
                                }
                                j = i + 16 | 0;
                                if ((c[j >> 2] | 0) == (k | 0)) {
                                    c[j >> 2] = g
                                } else {
                                    c[i + 20 >> 2] = g
                                }
                                if ((g | 0) == 0) {
                                    break b
                                }
                            }
                        } while (0);
                        if (g >>> 0 < (c[642] | 0) >>> 0) {
                            ma()
                        }
                        c[g + 24 >> 2] = i;
                        i = c[a + (h + 8) >> 2] | 0;
                        do {
                            if ((i | 0) != 0) {
                                if (i >>> 0 < (c[642] | 0) >>> 0) {
                                    ma()
                                } else {
                                    c[g + 16 >> 2] = i;
                                    c[i + 24 >> 2] = g;
                                    break
                                }
                            }
                        } while (0);
                        h = c[a + (h + 12) >> 2] | 0;
                        if ((h | 0) == 0) {
                            break
                        }
                        if (h >>> 0 < (c[642] | 0) >>> 0) {
                            ma()
                        } else {
                            c[g + 20 >> 2] = h;
                            c[h + 24 >> 2] = g;
                            break
                        }
                    }
                } while (0);
                c[b + 4 >> 2] = l | 1;
                c[m + l >> 2] = l;
                if ((b | 0) != (c[643] | 0)) {
                    break
                }
                c[640] = l;
                return
            } else {
                c[n >> 2] = o & -2;
                c[b + 4 >> 2] = l | 1;
                c[m + l >> 2] = l
            }
        } while (0);
        g = l >>> 3;
        if (l >>> 0 < 256 >>> 0) {
            a = g << 1;
            d = 2592 + (a << 2) | 0;
            h = c[638] | 0;
            g = 1 << g;
            do {
                if ((h & g | 0) == 0) {
                    c[638] = h | g;
                    f = d;
                    e = 2592 + (a + 2 << 2) | 0
                } else {
                    h = 2592 + (a + 2 << 2) | 0;
                    g = c[h >> 2] | 0;
                    if (g >>> 0 >= (c[642] | 0) >>> 0) {
                        f = g;
                        e = h;
                        break
                    }
                    ma()
                }
            } while (0);
            c[e >> 2] = b;
            c[f + 12 >> 2] = b;
            c[b + 8 >> 2] = f;
            c[b + 12 >> 2] = d;
            return
        }
        e = b;
        f = l >>> 8;
        do {
            if ((f | 0) == 0) {
                f = 0
            } else {
                if (l >>> 0 > 16777215 >>> 0) {
                    f = 31;
                    break
                }
                v = (f + 1048320 | 0) >>> 16 & 8;
                w = f << v;
                u = (w + 520192 | 0) >>> 16 & 4;
                w = w << u;
                f = (w + 245760 | 0) >>> 16 & 2;
                f = 14 - (u | v | f) + (w << f >>> 15) | 0;
                f = l >>> ((f + 7 | 0) >>> 0) & 1 | f << 1
            }
        } while (0);
        g = 2856 + (f << 2) | 0;
        c[b + 28 >> 2] = f;
        c[b + 20 >> 2] = 0;
        c[b + 16 >> 2] = 0;
        a = c[639] | 0;
        h = 1 << f;
        c: do {
            if ((a & h | 0) == 0) {
                c[639] = a | h;
                c[g >> 2] = e;
                c[b + 24 >> 2] = g;
                c[b + 12 >> 2] = b;
                c[b + 8 >> 2] = b
            } else {
                h = c[g >> 2] | 0;
                if ((f | 0) == 31) {
                    g = 0
                } else {
                    g = 25 - (f >>> 1) | 0
                }
                d: do {
                    if ((c[h + 4 >> 2] & -8 | 0) == (l | 0)) {
                        d = h
                    } else {
                        f = h;
                        h = l << g;
                        while (1) {
                            a = f + 16 + (h >>> 31 << 2) | 0;
                            g = c[a >> 2] | 0;
                            if ((g | 0) == 0) {
                                break
                            }
                            if ((c[g + 4 >> 2] & -8 | 0) == (l | 0)) {
                                d = g;
                                break d
                            } else {
                                f = g;
                                h = h << 1
                            }
                        }
                        if (a >>> 0 < (c[642] | 0) >>> 0) {
                            ma()
                        } else {
                            c[a >> 2] = e;
                            c[b + 24 >> 2] = f;
                            c[b + 12 >> 2] = b;
                            c[b + 8 >> 2] = b;
                            break c
                        }
                    }
                } while (0);
                f = d + 8 | 0;
                g = c[f >> 2] | 0;
                w = c[642] | 0;
                if (d >>> 0 >= w >>> 0 & g >>> 0 >= w >>> 0) {
                    c[g + 12 >> 2] = e;
                    c[f >> 2] = e;
                    c[b + 8 >> 2] = g;
                    c[b + 12 >> 2] = d;
                    c[b + 24 >> 2] = 0;
                    break
                } else {
                    ma()
                }
            }
        } while (0);
        w = (c[646] | 0) - 1 | 0;
        c[646] = w;
        if ((w | 0) == 0) {
            b = 3008
        } else {
            return
        }
        while (1) {
            b = c[b >> 2] | 0;
            if ((b | 0) == 0) {
                break
            } else {
                b = b + 8 | 0
            }
        }
        c[646] = -1;
        return
    }

    function dc(b, d, e) {
        b = b | 0;
        d = d | 0;
        e = e | 0;
        var f = 0;
        f = b | 0;
        if ((b & 3) == (d & 3)) {
            while (b & 3) {
                if ((e | 0) == 0) return f | 0;
                a[b] = a[d] | 0;
                b = b + 1 | 0;
                d = d + 1 | 0;
                e = e - 1 | 0
            }
            while ((e | 0) >= 4) {
                c[b >> 2] = c[d >> 2];
                b = b + 4 | 0;
                d = d + 4 | 0;
                e = e - 4 | 0
            }
        }
        while ((e | 0) > 0) {
            a[b] = a[d] | 0;
            b = b + 1 | 0;
            d = d + 1 | 0;
            e = e - 1 | 0
        }
        return f | 0
    }

    function ec(b) {
        b = b | 0;
        var c = 0;
        c = b;
        while (a[c] | 0) {
            c = c + 1 | 0
        }
        return c - b | 0
    }

    function fc(b, d, e) {
        b = b | 0;
        d = d | 0;
        e = e | 0;
        var f = 0,
            g = 0,
            h = 0,
            i = 0;
        f = b + e | 0;
        if ((e | 0) >= 20) {
            d = d & 255;
            i = b & 3;
            h = d | d << 8 | d << 16 | d << 24;
            g = f & ~3;
            if (i) {
                i = b + 4 - i | 0;
                while ((b | 0) < (i | 0)) {
                    a[b] = d;
                    b = b + 1 | 0
                }
            }
            while ((b | 0) < (g | 0)) {
                c[b >> 2] = h;
                b = b + 4 | 0
            }
        }
        while ((b | 0) < (f | 0)) {
            a[b] = d;
            b = b + 1 | 0
        }
        return b - e | 0
    }

    function gc(a, b) {
        a = a | 0;
        b = b | 0;
        Ma[a & 1](b | 0)
    }

    function hc(a, b, c) {
        a = a | 0;
        b = b | 0;
        c = c | 0;
        Na[a & 1](b | 0, c | 0)
    }

    function ic(a, b) {
        a = a | 0;
        b = b | 0;
        return Oa[a & 1](b | 0) | 0
    }

    function jc(a, b) {
        a = a | 0;
        b = +b;
        return +Pa[a & 7](+b)
    }

    function kc(a) {
        a = a | 0;
        Qa[a & 1]()
    }

    function lc(a, b, c) {
        a = a | 0;
        b = b | 0;
        c = c | 0;
        return Ra[a & 1](b | 0, c | 0) | 0
    }

    function mc(a) {
        a = a | 0;
        _(0)
    }

    function nc(a, b) {
        a = a | 0;
        b = b | 0;
        _(1)
    }

    function oc(a) {
        a = a | 0;
        _(2);
        return 0
    }

    function pc(a) {
        a = +a;
        _(3);
        return 0.0
    }

    function qc() {
        _(4)
    }

    function rc(a, b) {
        a = a | 0;
        b = b | 0;
        _(5);
        return 0
    }




    // EMSCRIPTEN_END_FUNCS
    var Ma = [mc, mc];
    var Na = [nc, nc];
    var Oa = [oc, oc];
    var Pa = [pc, pc, mb, pc, lb, pc, kb, pc];
    var Qa = [qc, qc];
    var Ra = [rc, rc];
    return {
        _firdes_get_window_from_string: ib,
        _strlen: ec,
        _firdes_lowpass_f: nb,
        _next_pow2: Mb,
        _gain_ff: Kb,
        _shift_table_cc: tb,
        _firdes_wkernel_hamming: lb,
        _fir_decimate_cc: ub,
        _encode_ima_adpcm_i16_u8: _b,
        _convert_i16_f: Sb,
        _shift_addition_init: Vb,
        _decimating_shift_addition_cc: Yb,
        _decimating_shift_addition_init: Xb,
        _shift_table_init: rb,
        _convert_u8_f: Qb,
        _fastagc_ff: Db,
        _memset: fc,
        _fmdemod_quadri_cf: Gb,
        _amdemod_cf: zb,
        _log2n: Lb,
        _convert_f_u8: Rb,
        _rational_resampler_get_lowpass_f: wb,
        _apply_fir_fft_cc: yb,
        _fractional_decimator_ff: xb,
        _amdemod_estimator_cf: Ab,
        _limit_ff: Jb,
        _fmdemod_atan_cf: Eb,
        _fmdemod_quadri_novect_cf: Fb,
        _shift_addition_cc: Ub,
        _firdes_wkernel_blackman: kb,
        _deemphasis_wfm_ff: Hb,
        _firdes_filter_len: pb,
        _decode_ima_adpcm_u8_i16: $b,
        _firdes_wkernel_boxcar: mb,
        _shift_math_cc: qb,
        _agc_ff: Zb,
        _dcblock_ff: Bb,
        _free: cc,
        _fastdcblock_ff: Cb,
        _firdes_get_string_from_window: jb,
        _rational_resampler_ff: vb,
        _convert_f_i16: Tb,
        _logpower_cf: Pb,
        _shift_addition_cc_test: Wb,
        _malloc: bc,
        _memcpy: dc,
        _deemphasis_nfm_ff: Ib,
        _apply_window_c: Nb,
        _shift_table_deinit: sb,
        _apply_window_f: Ob,
        _firdes_bandpass_c: ob,
        runPostSets: gb,
        stackAlloc: Sa,
        stackSave: Ta,
        stackRestore: Ua,
        setThrew: Va,
        setTempRet0: Ya,
        setTempRet1: Za,
        setTempRet2: _a,
        setTempRet3: $a,
        setTempRet4: ab,
        setTempRet5: bb,
        setTempRet6: cb,
        setTempRet7: db,
        setTempRet8: eb,
        setTempRet9: fb,
        dynCall_vi: gc,
        dynCall_vii: hc,
        dynCall_ii: ic,
        dynCall_ff: jc,
        dynCall_v: kc,
        dynCall_iii: lc
    }
})


// EMSCRIPTEN_END_ASM
({
    "Math": Math,
    "Int8Array": Int8Array,
    "Int16Array": Int16Array,
    "Int32Array": Int32Array,
    "Uint8Array": Uint8Array,
    "Uint16Array": Uint16Array,
    "Uint32Array": Uint32Array,
    "Float32Array": Float32Array,
    "Float64Array": Float64Array
}, {
    "abort": abort,
    "assert": assert,
    "asmPrintInt": asmPrintInt,
    "asmPrintFloat": asmPrintFloat,
    "min": Math_min,
    "invoke_vi": invoke_vi,
    "invoke_vii": invoke_vii,
    "invoke_ii": invoke_ii,
    "invoke_ff": invoke_ff,
    "invoke_v": invoke_v,
    "invoke_iii": invoke_iii,
    "_strncmp": _strncmp,
    "_fabsf": _fabsf,
    "_sysconf": _sysconf,
    "_abort": _abort,
    "_fprintf": _fprintf,
    "_printf": _printf,
    "_fflush": _fflush,
    "__reallyNegative": __reallyNegative,
    "_sqrtf": _sqrtf,
    "_fputc": _fputc,
    "_fabs": _fabs,
    "___setErrNo": ___setErrNo,
    "_fwrite": _fwrite,
    "_send": _send,
    "_write": _write,
    "_fputs": _fputs,
    "_log10": _log10,
    "_sin": _sin,
    "_ceilf": _ceilf,
    "__formatString": __formatString,
    "_cos": _cos,
    "_pwrite": _pwrite,
    "_puts": _puts,
    "_sbrk": _sbrk,
    "___errno_location": ___errno_location,
    "_atan2": _atan2,
    "_time": _time,
    "_strcmp": _strcmp,
    "STACKTOP": STACKTOP,
    "STACK_MAX": STACK_MAX,
    "tempDoublePtr": tempDoublePtr,
    "ABORT": ABORT,
    "NaN": NaN,
    "Infinity": Infinity
}, buffer);
var _firdes_get_window_from_string = Module["_firdes_get_window_from_string"] = asm["_firdes_get_window_from_string"];
var _strlen = Module["_strlen"] = asm["_strlen"];
var _firdes_lowpass_f = Module["_firdes_lowpass_f"] = asm["_firdes_lowpass_f"];
var _next_pow2 = Module["_next_pow2"] = asm["_next_pow2"];
var _gain_ff = Module["_gain_ff"] = asm["_gain_ff"];
var _shift_table_cc = Module["_shift_table_cc"] = asm["_shift_table_cc"];
var _firdes_wkernel_hamming = Module["_firdes_wkernel_hamming"] = asm["_firdes_wkernel_hamming"];
var _fir_decimate_cc = Module["_fir_decimate_cc"] = asm["_fir_decimate_cc"];
var _encode_ima_adpcm_i16_u8 = Module["_encode_ima_adpcm_i16_u8"] = asm["_encode_ima_adpcm_i16_u8"];
var _convert_i16_f = Module["_convert_i16_f"] = asm["_convert_i16_f"];
var _shift_addition_init = Module["_shift_addition_init"] = asm["_shift_addition_init"];
var _decimating_shift_addition_cc = Module["_decimating_shift_addition_cc"] = asm["_decimating_shift_addition_cc"];
var _decimating_shift_addition_init = Module["_decimating_shift_addition_init"] = asm["_decimating_shift_addition_init"];
var _shift_table_init = Module["_shift_table_init"] = asm["_shift_table_init"];
var _convert_u8_f = Module["_convert_u8_f"] = asm["_convert_u8_f"];
var _fastagc_ff = Module["_fastagc_ff"] = asm["_fastagc_ff"];
var _memset = Module["_memset"] = asm["_memset"];
var _fmdemod_quadri_cf = Module["_fmdemod_quadri_cf"] = asm["_fmdemod_quadri_cf"];
var _amdemod_cf = Module["_amdemod_cf"] = asm["_amdemod_cf"];
var _log2n = Module["_log2n"] = asm["_log2n"];
var _convert_f_u8 = Module["_convert_f_u8"] = asm["_convert_f_u8"];
var _rational_resampler_get_lowpass_f = Module["_rational_resampler_get_lowpass_f"] = asm["_rational_resampler_get_lowpass_f"];
var _apply_fir_fft_cc = Module["_apply_fir_fft_cc"] = asm["_apply_fir_fft_cc"];
var _fractional_decimator_ff = Module["_fractional_decimator_ff"] = asm["_fractional_decimator_ff"];
var _amdemod_estimator_cf = Module["_amdemod_estimator_cf"] = asm["_amdemod_estimator_cf"];
var _limit_ff = Module["_limit_ff"] = asm["_limit_ff"];
var _fmdemod_atan_cf = Module["_fmdemod_atan_cf"] = asm["_fmdemod_atan_cf"];
var _fmdemod_quadri_novect_cf = Module["_fmdemod_quadri_novect_cf"] = asm["_fmdemod_quadri_novect_cf"];
var _shift_addition_cc = Module["_shift_addition_cc"] = asm["_shift_addition_cc"];
var _firdes_wkernel_blackman = Module["_firdes_wkernel_blackman"] = asm["_firdes_wkernel_blackman"];
var _deemphasis_wfm_ff = Module["_deemphasis_wfm_ff"] = asm["_deemphasis_wfm_ff"];
var _firdes_filter_len = Module["_firdes_filter_len"] = asm["_firdes_filter_len"];
var _decode_ima_adpcm_u8_i16 = Module["_decode_ima_adpcm_u8_i16"] = asm["_decode_ima_adpcm_u8_i16"];
var _firdes_wkernel_boxcar = Module["_firdes_wkernel_boxcar"] = asm["_firdes_wkernel_boxcar"];
var _shift_math_cc = Module["_shift_math_cc"] = asm["_shift_math_cc"];
var _agc_ff = Module["_agc_ff"] = asm["_agc_ff"];
var _dcblock_ff = Module["_dcblock_ff"] = asm["_dcblock_ff"];
var _free = Module["_free"] = asm["_free"];
var _fastdcblock_ff = Module["_fastdcblock_ff"] = asm["_fastdcblock_ff"];
var _firdes_get_string_from_window = Module["_firdes_get_string_from_window"] = asm["_firdes_get_string_from_window"];
var _rational_resampler_ff = Module["_rational_resampler_ff"] = asm["_rational_resampler_ff"];
var _convert_f_i16 = Module["_convert_f_i16"] = asm["_convert_f_i16"];
var _logpower_cf = Module["_logpower_cf"] = asm["_logpower_cf"];
var _shift_addition_cc_test = Module["_shift_addition_cc_test"] = asm["_shift_addition_cc_test"];
var _malloc = Module["_malloc"] = asm["_malloc"];
var _memcpy = Module["_memcpy"] = asm["_memcpy"];
var _deemphasis_nfm_ff = Module["_deemphasis_nfm_ff"] = asm["_deemphasis_nfm_ff"];
var _apply_window_c = Module["_apply_window_c"] = asm["_apply_window_c"];
var _shift_table_deinit = Module["_shift_table_deinit"] = asm["_shift_table_deinit"];
var _apply_window_f = Module["_apply_window_f"] = asm["_apply_window_f"];
var _firdes_bandpass_c = Module["_firdes_bandpass_c"] = asm["_firdes_bandpass_c"];
var runPostSets = Module["runPostSets"] = asm["runPostSets"];
var dynCall_vi = Module["dynCall_vi"] = asm["dynCall_vi"];
var dynCall_vii = Module["dynCall_vii"] = asm["dynCall_vii"];
var dynCall_ii = Module["dynCall_ii"] = asm["dynCall_ii"];
var dynCall_ff = Module["dynCall_ff"] = asm["dynCall_ff"];
var dynCall_v = Module["dynCall_v"] = asm["dynCall_v"];
var dynCall_iii = Module["dynCall_iii"] = asm["dynCall_iii"];

Runtime.stackAlloc = function(size) {
    return asm['stackAlloc'](size)
};
Runtime.stackSave = function() {
    return asm['stackSave']()
};
Runtime.stackRestore = function(top) {
    asm['stackRestore'](top)
};

// Warning: printing of i64 values may be slightly rounded! No deep i64 math used, so precise i64 code not included
var i64Math = null;

// === Auto-generated postamble setup entry stuff ===

if (memoryInitializer) {
    function applyData(data) {
        HEAPU8.set(data, STATIC_BASE);
    }
    if (ENVIRONMENT_IS_NODE || ENVIRONMENT_IS_SHELL) {
        applyData(Module['readBinary'](memoryInitializer));
    } else {
        addRunDependency('memory initializer');
        Browser.asyncLoad(memoryInitializer, function(data) {
            applyData(data);
            removeRunDependency('memory initializer');
        }, function(data) {
            throw 'could not load memory initializer ' + memoryInitializer;
        });
    }
}

function ExitStatus(status) {
    this.name = "ExitStatus";
    this.message = "Program terminated with exit(" + status + ")";
    this.status = status;
};
ExitStatus.prototype = new Error();
ExitStatus.prototype.constructor = ExitStatus;

var initialStackTop;
var preloadStartTime = null;
var calledMain = false;

dependenciesFulfilled = function runCaller() {
    // If run has never been called, and we should call run (INVOKE_RUN is true, and Module.noInitialRun is not false)
    if (!Module['calledRun'] && shouldRunNow) run();
    if (!Module['calledRun']) dependenciesFulfilled = runCaller; // try this again later, after new deps are fulfilled
}

Module['callMain'] = Module.callMain = function callMain(args) {
    assert(runDependencies == 0, 'cannot call main when async dependencies remain! (listen on __ATMAIN__)');
    assert(__ATPRERUN__.length == 0, 'cannot call main when preRun functions remain to be called');

    args = args || [];

    if (ENVIRONMENT_IS_WEB && preloadStartTime !== null) {
        Module.printErr('preload time: ' + (Date.now() - preloadStartTime) + ' ms');
    }

    ensureInitRuntime();

    var argc = args.length + 1;

    function pad() {
        for (var i = 0; i < 4 - 1; i++) {
            argv.push(0);
        }
    }
    var argv = [allocate(intArrayFromString("/bin/this.program"), 'i8', ALLOC_NORMAL)];
    pad();
    for (var i = 0; i < argc - 1; i = i + 1) {
        argv.push(allocate(intArrayFromString(args[i]), 'i8', ALLOC_NORMAL));
        pad();
    }
    argv.push(0);
    argv = allocate(argv, 'i32', ALLOC_NORMAL);

    initialStackTop = STACKTOP;

    try {

        var ret = Module['_main'](argc, argv, 0);


        // if we're not running an evented main loop, it's time to exit
        if (!Module['noExitRuntime']) {
            exit(ret);
        }
    } catch (e) {
        if (e instanceof ExitStatus) {
            // exit() throws this once it's done to make sure execution
            // has been stopped completely
            return;
        } else if (e == 'SimulateInfiniteLoop') {
            // running an evented main loop, don't immediately exit
            Module['noExitRuntime'] = true;
            return;
        } else {
            if (e && typeof e === 'object' && e.stack) Module.printErr('exception thrown: ' + [e, e.stack]);
            throw e;
        }
    } finally {
        calledMain = true;
    }
}




function run(args) {
    args = args || Module['arguments'];

    if (preloadStartTime === null) preloadStartTime = Date.now();

    if (runDependencies > 0) {
        Module.printErr('run() called, but dependencies remain, so not running');
        return;
    }

    preRun();

    if (runDependencies > 0) return; // a preRun added a dependency, run will be called later
    if (Module['calledRun']) return; // run may have just been called through dependencies being fulfilled just in this very frame

    function doRun() {
        if (Module['calledRun']) return; // run may have just been called while the async setStatus time below was happening
        Module['calledRun'] = true;

        ensureInitRuntime();

        preMain();

        if (Module['_main'] && shouldRunNow) {
            Module['callMain'](args);
        }

        postRun();
    }

    if (Module['setStatus']) {
        Module['setStatus']('Running...');
        setTimeout(function() {
            setTimeout(function() {
                Module['setStatus']('');
            }, 1);
            if (!ABORT) doRun();
        }, 1);
    } else {
        doRun();
    }
}
Module['run'] = Module.run = run;

function exit(status) {
    ABORT = true;
    EXITSTATUS = status;
    STACKTOP = initialStackTop;

    // exit the runtime
    exitRuntime();

    // TODO We should handle this differently based on environment.
    // In the browser, the best we can do is throw an exception
    // to halt execution, but in node we could process.exit and
    // I'd imagine SM shell would have something equivalent.
    // This would let us set a proper exit status (which
    // would be great for checking test exit statuses).
    // https://github.com/kripken/emscripten/issues/1371

    // throw an exception to halt the current execution
    throw new ExitStatus(status);
}
Module['exit'] = Module.exit = exit;

function abort(text) {
    if (text) {
        Module.print(text);
        Module.printErr(text);
    }

    ABORT = true;
    EXITSTATUS = 1;

    throw 'abort() at ' + stackTrace();
}
Module['abort'] = Module.abort = abort;

// {{PRE_RUN_ADDITIONS}}

if (Module['preInit']) {
    if (typeof Module['preInit'] == 'function') Module['preInit'] = [Module['preInit']];
    while (Module['preInit'].length > 0) {
        Module['preInit'].pop()();
    }
}

// shouldRunNow refers to calling main(), not run().
var shouldRunNow = true;
if (Module['noInitialRun']) {
    shouldRunNow = false;
}

run();

// {{POST_RUN_ADDITIONS}}






// {{MODULE_ADDITIONS}}






// ========================================================== 
// ========= / THE CODE COMPILED BY EMCC ENDS HERE ==========
// ========================================================== 

asm$ = {
    malloc: function(type, size) {
        real_size = size * type.BYTES_PER_ELEMENT;
        pointer = Module._malloc(real_size);
        heap = new Uint8Array(Module.HEAPU8.buffer, pointer, real_size);
        return {
            asm$: true,
            ptr: heap.byteOffset,
            free: function() {
                Module._free(this.ptr);
            },
            arr: new type(heap.buffer, heap.byteOffset, size),
            size: size
        };
    },
    cpy: function(dst, dst_offset, src, src_offset, size) {
        if (typeof dst.asm$ != 'undefined') dst = dst.arr;
        if (typeof src.asm$ != 'undefined') src = src.arr;
        for (var i = 0; i < size; i++)
            dst[dst_offset + i] = src[src_offset + i];
    }
};

//                                                  void firdes_lowpass_f(float *output, int length, float cutoff_rate, window_t window)
firdes_lowpass_f = Module.cwrap('firdes_lowpass_f', null, ['number', 'number', 'number', 'number']);

//                                                            rational_resampler_ff_t rational_resampler_ff(float *input, float *output, int input_size, int interpolation, int decimation, float *taps, int taps_length, int last_taps_delay)
rational_resampler_ff = Module.cwrap('rational_resampler_ff', 'struct', ['number', 'number', 'number', 'number', 'number', 'number', 'number', 'number']);


rational_resampler_ff = function(pinput, poutput, input_length, interpolation, decimation, ptaps, taps_length, last_taps_delay) {
    stackbase = STACKTOP;
    STACKTOP += 4 * 3;
    _rational_resampler_ff(stackbase, pinput, poutput, input_length, interpolation, decimation, ptaps, taps_length, last_taps_delay);
    returnstruct = {
        input_processed: getValue(stackbase, 'i32'),
        output_size: getValue(stackbase + 4, 'i32'),
        last_taps_delay: getValue(stackbase + 8, 'i32')
    };
    STACKTOP = stackbase;
    return returnstruct;
}

sdrjs = {};

sdrjs.WINDOW_BOXCAR = 0;
sdrjs.WINDOW_BLACKMAN = 1;
sdrjs.WINDOW_HAMMING = 2;

//this will be impportant whil converting arrays
//http://stackoverflow.com/questions/25839216/convert-float32array-to-int16array

/*sdrjs.prototype.FirdesLowpassF=function(taps_length,transition_bw,window)
{
	this.calculate=function(){}
	this.get_output=function(){}
	this.get_output_heap=function(){}
};*/


sdrjs.ConvertI16_F = function(i16data) {
    var f32data = new Float32Array(i16data.length);
    for (var i = 0; i < i16data.length; i++) f32data[i] = i16data[i] / 32768;
    return f32data;
}

ima_adpcm_codec = function(encode, pinput, poutput, input_length, state) {
    myfunc = (encode) ? _encode_ima_adpcm_i16_u8 : _decode_ima_adpcm_u8_i16;
    stackbase = STACKTOP;
    STACKTOP += 4 * 2; //sizeof(int)*2
    myfunc(stackbase, pinput, poutput, input_length, state.ptr);
    state.arr[0] = getValue(stackbase + 0, 'i32');
    state.arr[1] = getValue(stackbase + 4, 'i32');
    STACKTOP = stackbase;
};

sdrjs.ImaAdpcm = function() {
    this.BUFSIZE = 1024 * 64;
    this.ima_adpcm_state = asm$.malloc(Int32Array, 2);
    this.i16_buffer = asm$.malloc(Int16Array, this.BUFSIZE * 2);
    this.u8_buffer = asm$.malloc(Uint8Array, this.BUFSIZE);
    this.ima_adpcm_state.arr[0] = 0;
    this.ima_adpcm_state.arr[1] = 0;

    this.encode = function(data) {
        //not_tested_yet
        asm$.cpy(this.i16_buffer.arr, 0, data, 0, data.length);
        ima_adpcm_codec(true, this.i16_buffer.ptr, this.u8_buffer.ptr, data.length, this.ima_adpcm_state);
        out = new Uint8Array(data.length / 2);
        asm$.cpy(out, 0, this.u8_buffer, 0, data.length / 2);
        return out;
    };

    this.decode = function(data) {
        asm$.cpy(this.u8_buffer.arr, 0, data, 0, data.length);
        ima_adpcm_codec(false, this.u8_buffer.ptr, this.i16_buffer.ptr, data.length, this.ima_adpcm_state);
        out = new Int16Array(data.length * 2);
        asm$.cpy(out, 0, this.i16_buffer.arr, 0, data.length * 2);
        return out;
    };
    this.reset = function() {
        this.ima_adpcm_state.arr[0] = this.ima_adpcm_state.arr[1] = 0 | 0;
    }
};

sdrjs.REBUFFER_FIXED = 0; //rebuffer should return arrays of fixed size
sdrjs.REBUFFER_MAX = 1; //rebuffer should return arrays with a maximal size of the parameter size

sdrjs.Rebuffer = function(size, mode) {
    this.mode = mode;
    this.size = size;
    this.total_size = 0;
    this.arrays = [];
    this.last_arr = [];
    this.last_arr_offset = 0;
    this.push = function(data) {
        this.total_size += data.length;
        this.arrays.push(data);
    };
    this.remaining = function() {
        var fixed_bufs_num = Math.floor(this.total_size / this.size);
        if (!this.mode) return fixed_bufs_num;
        else return fixed_bufs_num + (!!(this.total_size - fixed_bufs_num * this.size)); //if REBUFFER_MAX, add one if we could return one more buffer (smaller than the fixed size)
    };
    this.take = function() {
        var a = this._take(); /*console.log(a);*/
        return a;
    };
    this._take = function() {
        var remain = this.size;
        var offset = 0;
        var obuf = new Float32Array(size);
        //console.log("==== get new obuf ====", size);
        while (remain) {
            if (this.last_arr_offset == this.last_arr.length) {
                if (this.arrays.length == 0) {
                    //console.log("this should not happen");
                    if (this.mode) //REBUFFER_MAX
                    {
                        this.total_size = 0;
                        return obuf.subarray(0, offset);
                    } else return new Float32Array(0); //REBUFFER_FIXED
                }
                //console.log("pick new last_arr");
                this.last_arr = this.arrays.shift();
                this.last_arr_offset = 0;
            }
            var rwithin = this.last_arr.length - this.last_arr_offset;
            //console.log("b :: ","remain", remain, "rwithin",rwithin,"last_arr.length",this.last_arr.length,"larroffset",this.last_arr_offset,"offset",offset);
            if (remain < rwithin) {
                //console.log("remain < rwithin"); //seems problematic @Andris
                for (var i = 0; i < remain; i++) obuf[offset++] = this.last_arr[this.last_arr_offset++];
                remain = 0;
            } else {
                //console.log("remain > rwithin");
                for (var i = 0; i < rwithin; i++) obuf[offset++] = this.last_arr[this.last_arr_offset++];
                remain -= rwithin;
            }
            //console.log("e :: ","remain", remain, "rwithin",rwithin,"last_arr.length",this.last_arr.length,"larroffset",this.last_arr_offset,"offset",offset);
        }

        this.total_size -= obuf.length;
        //console.log("return _take");
        return obuf;
    };
};

sdrjs.RationalResamplerFF = function(interpolation, decimation, transition_bw, window) {
    this.interpolation = interpolation;
    this.decimation = decimation;
    this.transition_bw = (typeof transition_bw == 'undefined') ? 0.05 : transition_bw;
    this.window = (typeof window == 'undefined') ? 1 : window;
    this.buffer_size = 1024 * 512;
    this.output_buffer_size = Math.floor((this.buffer_size * interpolation) / decimation);
    this.input_buffer = asm$.malloc(Float32Array, this.buffer_size);
    this.output_buffer = asm$.malloc(Float32Array, this.output_buffer_size);
    //Calculate filter
    this.taps_length = Math.floor(4 / this.transition_bw);
    this.taps = asm$.malloc(Float32Array, this.taps_length);
    var cutoff_for_interpolation = 1.0 / interpolation;
    var cutoff_for_decimation = 1.0 / decimation;
    var cutoff = (cutoff_for_interpolation < cutoff_for_decimation) ? cutoff_for_interpolation : cutoff_for_decimation; //get the lower
    firdes_lowpass_f(this.taps.ptr, this.taps_length, cutoff / 2, window);

    this.remain = 0;
    this.remain_offset = 0;
    this.last_taps_delay = 0;

    this.process = function(input) {

        if (input.length + this.remain > this.buffer_size) {
            return new Float32Array(0);
            console.log("sdrjs.RationalResamplerFF: critical audio buffering error"); //This should not happen...
            /*	console.log("RationalResamplerFF: splitting..."); //TODO: this branch has not been checked
			output_buffers=Array();
			new_buffer_size=this.buffer_size/2;
			i=0;
			//process the input in chunks of new_buffer_size, and add the output product Float32Array-s to output_buffers.
			while((i++)*new_buffer_size<=input.length)
			{
				output_buffers.push(this._process_noheapcheck(input.subarray(i*new_buffer_size,(i+1)*new_buffer_size)));
			}
			//add up the sizes of the output_buffer-s.
			total_output_length=0;
			output_buffers.forEach(function(a){total_output_length+=a.length;});
			//create one big buffer from concatenating the output_buffer-s
			output=new Float32Array(total_output_length);
			output_pos=0;
			output_buffers.forEach(function(a){
				asm$.cpy(output,output_pos,a,0,a.length);
				output_pos+=a.length;
			});
			return output;*/
        } else return this._process_noheapcheck(input);
    };
    this._process_noheapcheck = function(input) //if we are sure we have enough space in the buffers 
        {
            asm$.cpy(this.input_buffer.arr, 0, this.input_buffer.arr, this.remain_offset, this.remain);
            asm$.cpy(this.input_buffer.arr, this.remain, input, 0, input.length);
            var total_input_size = input.length + this.remain;
            d = rational_resampler_ff(this.input_buffer.ptr, this.output_buffer.ptr, total_input_size, this.interpolation, this.decimation, this.taps.ptr, this.taps_length, this.last_taps_delay);
            this.last_taps_delay = d.last_taps_delay;
            this.remain = total_input_size - d.input_processed;
            this.remain_offset = d.input_processed;
            var output_copy_arr = new Float32Array(d.output_size);
            asm$.cpy(output_copy_arr, 0, this.output_buffer.arr, 0, d.output_size);
            return output_copy_arr;
        };
};


_sdrjs_logb = function(what) {
    document.body.innerHTML += what + "<br />";
}


function test_firdes_lowpass_f_original() {
    //Original method explained over here: 
    //http://kapadia.github.io/emscripten/2013/09/13/emscripten-pointers-and-pointers.html
    _sdrjs_logb("test_firdes_lowpass_f_original():");
    _sdrjs_logb("Now designing FIR filter with firdes_lowpass_f in sdr.js...");
    _sdrjs_logb("output should be the same as: <strong>csdr firdes_lowpass_f 0.1 101 HAMMING</strong>");

    var outputSize = 101 * 4;
    var outputPtr = Module._malloc(outputSize);
    var outputHeap = new Uint8Array(Module.HEAPU8.buffer, outputPtr, outputSize);
    firdes_lowpass_f(outputHeap.byteOffset, 101, 0.1, 2);
    var output = new Float32Array(outputHeap.buffer, outputHeap.byteOffset, 101);
    outputStr = String();
    for (i = 0; i < output.length; i++) outputStr += output[i].toFixed(6) + ", ";
    Module._free(outputHeap.byteOffset);
    _sdrjs_logb(outputStr);
}


function test_firdes_lowpass_f_new() {
    //This is much simpler, using asm$
    _sdrjs_logb("test_firdes_lowpass_f_new():");
    _sdrjs_logb("Now designing FIR filter with firdes_lowpass_f in sdr.js...");
    _sdrjs_logb("output should be the same as: <strong>csdr firdes_lowpass_f 0.1 101 HAMMING</strong>");

    output = asm$.malloc(Float32Array, 101);
    firdes_lowpass_f(output.ptr, 101, 0.1, 2);
    outputStr = String();
    for (i = 0; i < output.arr.length; i++) outputStr += (output.arr[i]).toFixed(6) + ", ";
    output.free();
    _sdrjs_logb(outputStr);
}

function test_struct_return_value() {
    v = STACKTOP;
    STACKTOP += 4 * 3;
    _shift_addition_init(v, 0.2);
    console.log(
        "sinval=", getValue(v, 'float'),
        "cosval=", getValue(v + 4, 'float'),
        "rate=", getValue(v + 8, 'float')
    );
    STACKTOP = v;
}