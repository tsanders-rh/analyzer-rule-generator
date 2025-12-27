# Angular Modernization Detection Patterns

Patterns to detect code that should be migrated to modern Angular syntax.

## Legacy @Input Decorators (Angular 17+)

**Pattern:** Detect @Input() decorators that should be migrated to input() signals
**Detection:** Look for @Input in component files

```typescript
// Legacy pattern to detect
@Input() name: string;
@Input() age?: number;
@Input({ required: true }) id!: string;

// Modern equivalent (for reference)
name = input<string>('');
age = input<number>();
id = input.required<string>();
```

## Legacy @Output Decorators (Angular 17+)

**Pattern:** Detect @Output() decorators that should be migrated to output() function
**Detection:** Look for @Output in component files

```typescript
// Legacy pattern to detect
@Output() nameChange = new EventEmitter<string>();

// Modern equivalent (for reference)
nameChange = output<string>();
```

## Legacy @ViewChild/@ContentChild (Angular 17+)

**Pattern:** Detect query decorators that should be migrated to signal queries
**Detection:** Look for @ViewChild, @ContentChild in component files

```typescript
// Legacy patterns to detect
@ViewChild('myRef') myRef?: ElementRef;
@ViewChild(ChildComponent, { static: true }) child!: ChildComponent;
@ContentChild('content') content?: TemplateRef<any>;

// Modern equivalents (for reference)
myRef = viewChild<ElementRef>('myRef');
child = viewChild.required(ChildComponent);
content = contentChild<TemplateRef<any>>('content');
```

## Legacy Template Directives (Angular 17+)

**Pattern:** Detect *ngIf, *ngFor, *ngSwitch in templates
**Detection:** Look for structural directives in .html files

```html
<!-- Legacy patterns to detect -->
<div *ngIf="condition">Content</div>
<div *ngFor="let item of items">{{ item }}</div>
<div [ngSwitch]="value">...</div>

<!-- Modern equivalents (for reference) -->
@if (condition) { <div>Content</div> }
@for (item of items; track item) { <div>{{ item }}</div> }
@switch (value) { ... }
```

## Legacy NgClass Directive (Angular 11+)

**Pattern:** Detect [ngClass] usage that should use class bindings
**Detection:** Look for [ngClass] in templates

```html
<!-- Legacy pattern to detect -->
<div [ngClass]="{ 'active': isActive, 'disabled': isDisabled }">

<!-- Modern equivalent (for reference) -->
<div [class.active]="isActive" [class.disabled]="isDisabled">
```

## Legacy NgStyle Directive (Angular 11+)

**Pattern:** Detect [ngStyle] usage that should use style bindings
**Detection:** Look for [ngStyle] in templates

```html
<!-- Legacy pattern to detect -->
<div [ngStyle]="{ 'color': textColor, 'font-size': fontSize }">

<!-- Modern equivalent (for reference) -->
<div [style.color]="textColor" [style.font-size]="fontSize">
```

## Non-Standalone Components (Angular 14+)

**Pattern:** Detect components without standalone: true
**Detection:** Look for @Component without standalone property

```typescript
// Legacy pattern to detect
@Component({
  selector: 'app-my',
  template: '...'
})
export class MyComponent { }

// Modern equivalent (for reference)
@Component({
  selector: 'app-my',
  template: '...',
  standalone: true,
  imports: [...]
})
export class MyComponent { }
```

## Constructor-Based Dependency Injection (Angular 14+)

**Pattern:** Detect constructor DI that could use inject()
**Detection:** Look for constructor with dependencies in components/services

```typescript
// Legacy pattern to detect
export class MyComponent {
  constructor(private myService: MyService, private http: HttpClient) {}
}

// Modern equivalent (for reference)
export class MyComponent {
  private myService = inject(MyService);
  private http = inject(HttpClient);
}
```

## RouterTestingModule in Tests (Angular 16+)

**Pattern:** Detect RouterTestingModule imports in test files
**Detection:** Look for RouterTestingModule in .spec.ts files

```typescript
// Legacy pattern to detect
import { RouterTestingModule } from '@angular/router/testing';

TestBed.configureTestingModule({
  imports: [RouterTestingModule]
});

// Modern equivalent (for reference)
import { provideRouter } from '@angular/router';
import { provideLocationMocks } from '@angular/common/testing';

TestBed.configureTestingModule({
  providers: [provideRouter([]), provideLocationMocks()]
});
```

## CommonModule in Standalone Components (Angular 14+)

**Pattern:** Detect CommonModule import in standalone components
**Detection:** Look for CommonModule in imports array of standalone components

```typescript
// Legacy pattern to detect
@Component({
  standalone: true,
  imports: [CommonModule]
})

// Modern equivalent (for reference)
@Component({
  standalone: true,
  imports: [NgIf, NgFor, AsyncPipe, DatePipe]
})
```
