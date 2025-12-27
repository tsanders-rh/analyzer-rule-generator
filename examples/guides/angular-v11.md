# Angular Migration Guide: v11

Router improvements and ViewEncapsulation updates.

ng update @angular/core@11 @angular/cli@11
which should bring you to version 11 of Angular.
Basic
Run
ng update @angular/material@11
.
Basic
Angular now requires
TypeScript 4.0
.
ng update
will migrate you automatically.
Basic
Support for IE9, IE10, and IE mobile has been removed. This was announced in the
v10 update
.
Basic
You can now opt-in to use webpack 5 by using Yarn and adding
"resolutions": {"webpack": "^5.0.0"}
to your
package.json
.
Medium
When generating new projects, you will be asked if you want to enable strict mode. This will configure TypeScript and the Angular compiler for stricter type checking, and apply smaller bundle budgets by default. You can use the
--strict=true
or
--strict=false
to skip the prompt.
Medium
If you use the router, the default value of
relativeLinkResolution
has changed from
legacy
to
corrected
. If your application previously used the default by not specifying a value in the
ExtraOptions
and uses relative links when navigating from children of empty path routes, you will need to update your
RouterModule
's configuration to specifically specify
legacy
for
relativeLinkResolution
. See
the documentation
for more details.
Advanced
In the Angular Router, the options deprecated in v4 for
initialNavigation
have been removed. If you previously used
enabled
or
true
, now choose
enabledNonBlocking
or
enabledBlocking
. If you previously used
false
or
legacy_disabled
, now use
disabled
.
Advanced
In the Angular Router's
routerLink
,
preserveQueryParams
has been removed, use
queryParamsHandling="preserve"
instead.
Medium
If you were accessing the
routerLink
values of
queryParams
,
fragment
or
queryParamsHandling
you might need to relax the typing to also accept
undefined
and
null
.
Advanced
The component view encapsulation option
ViewEncapsulation.Native
has been removed. Use
ViewEncapsulation.ShadowDom
instead.
ng update
will migrate you automatically.
Advanced
If you use i18n, expressions within International Components for Unicode (ICUs) expressions are now type-checked again. This may cause compilation failures if errors are found in expressions that appear within an ICU.
Advanced
Directives in the
@angular/forms
package used to have
any[]
as the type of the expected
validators
and
asyncValidators
arguments in constructors. Now these arguments are properly typed, so if your code relies on form's directive constructor types it may require some updates to improve type safety.
Advanced
If you use Angular Forms, the type of
AbstractFormControl.parent
now includes null.
ng update
will migrate you automatically, but in an unlikely case your code was testing the parent against undefined with strict equality, you'll need to change this to
=== null
instead, since the parent is now explicitly initialized with
null
instead of being left undefined.
Advanced
The rarely used
@angular/platform-webworker
and
@angular/platform-webworker-dynamic
were deprecated in v8 and have been removed. Running parts of Angular in a web worker was an experiment that never worked well for common use cases. Angular still has great support for
Web Workers
.
Advanced
The
slice
pipe now returns null for the undefined input value, which is consistent with the behavior of most pipes.
Advanced
The
keyvalue
pipe has been fixed to report that for input objects that have number keys, the result type will contain the string representation of the keys. This was already the case and the code has simply been updated to reflect this. Please update the consumers of the pipe output if they were relying on the incorrect types. Note that this does not affect use cases where the input values are
Map
s, so if you need to preserve
number
s, this is an effective way.
Advanced
The number pipes (
decimal
,
percent
,
currency
, etc) now explicitly state which types are accepted.
Advanced
The
date
pipe now explicitly states which types are accepted.
Advanced
When passing a date-time formatted string to the
DatePipe
in a format that contains fractions of a millisecond, the milliseconds will now always be rounded down rather than to the nearest millisecond. Most applications will not be affected by this change. If this is not the desired behaviour then consider pre-processing the string to round the millisecond part before passing it to the
DatePipe
.
Advanced
The
async
pipe no longer claims to return undefined for an input that was typed as undefined. Note that the code actually returned null on undefined inputs.
Advanced
The
uppercase
and
lowercase
pipes no longer let falsy values through. They now map both
null
and
undefined
to
null
and raise an exception on invalid input (
0
,
false
,
NaN
). This matches other Angular pipes.
Medium
If you use the router with
NavigationExtras
, new typings allow a variable of type
NavigationExtras
to be passed in, but they will not allow object literals, as they may only specify known properties. They will also not accept types that do not have properties in common with the ones in the
Pick
. If you are affected by this change, only specify properties from the NavigationExtras which are actually used in the respective function calls or use a type assertion on the object or variable:
as NavigationExtras
.
Advanced
In your tests if you call
TestBed.overrideProvider
after TestBed initialization, provider overrides are no longer applied. This behavior is consistent with other override methods (such as
TestBed.overrideDirective
, etc) but they throw an error to indicate that. The check was previously missing in the TestBed.overrideProvider function. If you see this error, you should move
TestBed.overrideProvider
calls before TestBed initialization is completed.
Medium
If you use the Router's RouteReuseStrategy, the argument order has changed. When calling
RouteReuseStrategy#shouldReuseRoute
previously when evaluating child routes, they would be called with the
future
and
current
arguments swapped. If your
RouteReuseStrategy
relies specifically on only the future or current snapshot state, you may need to update the
shouldReuseRoute
implementation's use of
future
and
current
ActivateRouteSnapshots
.
Medium
If you use locale data arrays, this API will now return readonly arrays. If you were mutating them (e.g. calling
sort()
,
push()
,
splice()
, etc) then your code will not longer compile. If you need to mutate the array, you should now take a copy (e.g. by calling
slice()
) and mutate the copy.
Advanced
In change detection,
CollectionChangeRecord
has been removed, use
IterableChangeRecord
instead.
Advanced
If you use Angular Forms with async validators defined at initialization time on class instances of
FormControl
,
FormGroup
or
FormArray
, the status change event was not previously emitted once async validator completed. This has been changed so that the status event is emitted into the
statusChanges
observable. If your code relies on the old behavior, you can filter/ignore this additional status change event.
Medium
Run
