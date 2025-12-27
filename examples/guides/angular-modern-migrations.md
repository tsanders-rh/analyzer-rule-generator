# Angular Modern Migrations Reference

Source: https://angular.dev/reference/migrations

## Standalone Components

**Migration:** Convert NgModule-based components to standalone
**Affects:** *.ts component files
**Version:** Angular 14+

Before:
```typescript
@NgModule({
  declarations: [MyComponent],
  imports: [CommonModule, RouterModule]
})
export class MyModule { }

@Component({
  selector: 'app-my',
  template: '...'
})
export class MyComponent { }
```

After:
```typescript
@Component({
  selector: 'app-my',
  template: '...',
  standalone: true,
  imports: [CommonModule, RouterModule]
})
export class MyComponent { }
```

## Control Flow Syntax

**Migration:** Replace structural directives with built-in control flow
**Affects:** *.html template files
**Version:** Angular 17+

### *ngIf → @if

Before:
```html
<div *ngIf="condition">Content</div>
<div *ngIf="condition; else other">Content</div>
<ng-template #other>Other content</ng-template>
```

After:
```html
@if (condition) {
  <div>Content</div>
}

@if (condition) {
  <div>Content</div>
} @else {
  <div>Other content</div>
}
```

### *ngFor → @for

Before:
```html
<div *ngFor="let item of items; track item.id">
  {{ item.name }}
</div>
```

After:
```html
@for (item of items; track item.id) {
  <div>{{ item.name }}</div>
}
```

### *ngSwitch → @switch

Before:
```html
<div [ngSwitch]="value">
  <div *ngSwitchCase="'a'">Case A</div>
  <div *ngSwitchCase="'b'">Case B</div>
  <div *ngSwitchDefault>Default</div>
</div>
```

After:
```html
@switch (value) {
  @case ('a') { <div>Case A</div> }
  @case ('b') { <div>Case B</div> }
  @default { <div>Default</div> }
}
```

## inject() Function

**Migration:** Replace constructor-based DI with inject() function
**Affects:** *.ts component/service files
**Version:** Angular 14+

Before:
```typescript
export class MyComponent {
  constructor(private myService: MyService) {}
}
```

After:
```typescript
export class MyComponent {
  private myService = inject(MyService);
}
```

## Signal Inputs

**Migration:** Convert @Input() to input() signals
**Affects:** *.ts component files
**Version:** Angular 17+

Before:
```typescript
@Component({...})
export class MyComponent {
  @Input() name: string;
  @Input() age?: number;
  @Input({ required: true }) id!: string;
}
```

After:
```typescript
@Component({...})
export class MyComponent {
  name = input<string>('');
  age = input<number>();
  id = input.required<string>();
}
```

## Signal Outputs

**Migration:** Convert @Output() to output() function
**Affects:** *.ts component files
**Version:** Angular 17+

Before:
```typescript
@Component({...})
export class MyComponent {
  @Output() nameChange = new EventEmitter<string>();
  
  updateName(name: string) {
    this.nameChange.emit(name);
  }
}
```

After:
```typescript
@Component({...})
export class MyComponent {
  nameChange = output<string>();
  
  updateName(name: string) {
    this.nameChange.emit(name);
  }
}
```

## Signal Queries

**Migration:** Convert @ViewChild/@ContentChild to viewChild()/contentChild()
**Affects:** *.ts component files
**Version:** Angular 17+

Before:
```typescript
@Component({...})
export class MyComponent {
  @ViewChild('myRef') myRef?: ElementRef;
  @ViewChild(ChildComponent, { static: true }) child!: ChildComponent;
  @ContentChild('content') content?: TemplateRef<any>;
}
```

After:
```typescript
@Component({...})
export class MyComponent {
  myRef = viewChild<ElementRef>('myRef');
  child = viewChild.required(ChildComponent);
  content = contentChild<TemplateRef<any>>('content');
}
```

## RouterTestingModule Migration

**Migration:** Replace RouterTestingModule with RouterModule
**Affects:** *.spec.ts test files
**Version:** Angular 16+

Before:
```typescript
import { RouterTestingModule } from '@angular/router/testing';

TestBed.configureTestingModule({
  imports: [RouterTestingModule]
});
```

After:
```typescript
import { provideRouter } from '@angular/router';
import { provideLocationMocks } from '@angular/common/testing';

TestBed.configureTestingModule({
  providers: [
    provideRouter([]),
    provideLocationMocks()
  ]
});
```

## NgClass to Class Bindings

**Migration:** Convert NgClass to native class bindings
**Affects:** *.html template files
**Version:** Angular 11+

Before:
```html
<div [ngClass]="{ 'active': isActive, 'disabled': isDisabled }">
<div [ngClass]="['class1', 'class2']">
```

After:
```html
<div [class.active]="isActive" [class.disabled]="isDisabled">
<div class="class1 class2">
```

## NgStyle to Style Bindings

**Migration:** Convert NgStyle to native style bindings
**Affects:** *.html template files
**Version:** Angular 11+

Before:
```html
<div [ngStyle]="{ 'color': textColor, 'font-size': fontSize }">
```

After:
```html
<div [style.color]="textColor" [style.font-size]="fontSize">
```

## CommonModule to Standalone Imports

**Migration:** Import specific directives instead of CommonModule
**Affects:** *.ts component files
**Version:** Angular 14+ (for standalone)

Before:
```typescript
@Component({
  standalone: true,
  imports: [CommonModule]
})
```

After:
```typescript
@Component({
  standalone: true,
  imports: [NgIf, NgFor, NgSwitch, AsyncPipe, DatePipe]
})
```

## Self-closing Tags

**Migration:** Use self-closing tags for components without content
**Affects:** *.html template files
**Version:** Angular 15+

Before:
```html
<app-header></app-header>
<app-footer></app-footer>
```

After:
```html
<app-header />
<app-footer />
```
