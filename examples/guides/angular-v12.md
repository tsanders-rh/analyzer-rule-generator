# Angular Migration Guide: v12

Forms validation and i18n message ID migration.

ng update @angular/core@12 @angular/cli@12
which should bring you to version 12 of Angular.
Basic
Run
ng update @angular/material@12
.
Basic
Angular now requires
TypeScript 4.2
.
ng update
will update you automatically.
Basic
IE11 support has been deprecated. Find details in the
RFC for IE11 removal
.
Basic
You can no longer use Angular with Node.js version 10 or older
Basic
Change the import of
XhrFactory
from
@angular/common/http
to
@angular/common
.
Medium
If you rely on legacy i18n message IDs use the
localize-migrate
tool to
move away from them
.
Medium
If you are using
emitDistinctChangesOnly
to configure
@ContentChildren
and
@ViewChildren
queries, you may need to update its value to
false
to align with its previous behavior. In v12
emitDistinctChangesOnly
has default value
true
, and in future releases we will remove this configuration option to prevent triggering of unnecessary changes.
Medium
You can run the optional migration for enabling production builds by default
ng update @angular/cli@12 --migrate-only production-by-default
.
Medium
If you  use Angular forms,
min
and
max
attributes on
<input type="number">
will now trigger validation logic.
Advanced
If your app has custom classes that extend
FormArray
or
FormGroup
classes and override the above-mentioned methods, you may need to update your implementation
Advanced
Update zone.js to version 0.11.4.
ng update
will update this dependency automatically.
Advanced
If you extend the
HttpParams
class you may have to update the signature of its method to reflect changes in the parameter types.
Advanced
routerLinkActiveOptions
property of
RouterLinkActive
now has a more specific type. You may need to update code accessing this property to align with the changes.
Advanced
The initializer callbacks now have more specific return types, which may require update of your code if you are getting an
APP_INITIALIZER
instance via
Injector.get
or
TestBed.inject
.
Advanced
The router fragments now could be
null
. Add
null
checks to avoid TypeScript failing with type errors.
Advanced
Make sure you don't rely on
ng.getDirectives
throwing an error if it can't find a directive associated with a particular DOM node.
Advanced
Check out
optimization.styles.inlineCritical
option in your angular.json file. It now defaults to
true
. Remember that the whole
optimization
option can be set as boolean which will set all the suboptions to defaults.
Advanced
Run
