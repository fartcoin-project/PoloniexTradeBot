// noinspection JSDeprecatedSymbols

import {NgModule} from '@angular/core';
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';
import {ReactiveFormsModule} from '@angular/forms';
import {FormlyFieldConfig, FormlyModule} from '@ngx-formly/core';
import {FormlyBootstrapModule} from '@ngx-formly/bootstrap';
import {HttpClientModule} from '@angular/common/http';
import {MatMenuModule} from '@angular/material/menu';
import {FormlyJsonComponent} from './formly-json.component';
import {ArrayTypeComponent} from './array.type';
import {ObjectTypeComponent} from './object.type';
import {MultiSchemaTypeComponent} from './multischema.type';
import {NullTypeComponent} from './null.type';

export function minItemsValidationMessage(err: any, field: FormlyFieldConfig) {
  const {templateOptions} = field;
  return `should NOT have fewer than ${templateOptions ? templateOptions : ['minItems']} items`;
}

export function maxItemsValidationMessage(err: any, field: FormlyFieldConfig) {
  const {templateOptions} = field;
  return `should NOT have more than ${templateOptions ? templateOptions : ['maxItems']} items`;
}

export function minlengthValidationMessage(err: any, {templateOptions}: FormlyFieldConfig) {
  // @ts-ignore
  let s = `should NOT be shorter than ${templateOptions.minLength} characters`;
  return s;
}

export function maxlengthValidationMessage(err: any, field: FormlyFieldConfig) {
  // @ts-ignore
  return `should NOT be longer than ${field.templateOptions.maxLength} characters`;
}

export function minValidationMessage(err: any, field: FormlyFieldConfig) {
  // @ts-ignore
  return `should be >= ${field.templateOptions.min}`;
}

export function maxValidationMessage(err: any, field: FormlyFieldConfig) {
  // @ts-ignore
  return `should be <= ${field.templateOptions.max}`;
}

export function multipleOfValidationMessage(err: any, field: FormlyFieldConfig) {
  // @ts-ignore
  return `should be multiple of ${field.templateOptions.step}`;
}

export function exclusiveMinimumValidationMessage(err: any, field: FormlyFieldConfig) {
  // @ts-ignore
  return `should be > ${field.templateOptions.step}`;
}

export function exclusiveMaximumValidationMessage(err: any, field: FormlyFieldConfig) {
  // @ts-ignore
  return `should be < ${field.templateOptions.step}`;
}

export function constValidationMessage(err: any, field: FormlyFieldConfig) {
  const {templateOptions} = field;
  return `should be equal to constant "${templateOptions ? templateOptions : ['const']}"`;
}

@NgModule({
  imports: [
    BrowserAnimationsModule,
    ReactiveFormsModule,
    FormlyBootstrapModule,
    HttpClientModule,
    MatMenuModule,
    FormlyModule.forRoot({
      validationMessages: [
        { name: 'required', message: 'This field is required' },
        { name: 'null', message: 'should be null' },
        { name: 'minlength', message: minlengthValidationMessage },
        { name: 'maxlength', message: maxlengthValidationMessage },
        { name: 'min', message: minValidationMessage },
        { name: 'max', message: maxValidationMessage },
        { name: 'multipleOf', message: multipleOfValidationMessage },
        { name: 'exclusiveMinimum', message: exclusiveMinimumValidationMessage },
        { name: 'exclusiveMaximum', message: exclusiveMaximumValidationMessage },
        { name: 'minItems', message: minItemsValidationMessage },
        { name: 'maxItems', message: maxItemsValidationMessage },
        { name: 'uniqueItems', message: 'should NOT have duplicate items' },
        { name: 'const', message: constValidationMessage },
      ],
      types: [
        { name: 'string', extends: 'input' },
        {
          name: 'number',
          extends: 'input',
          defaultOptions: {
            templateOptions: {
              type: 'number',
            },
          },
        },
        {
          name: 'integer',
          extends: 'input',
          defaultOptions: {
            templateOptions: {
              type: 'number',
            },
          },
        },
        { name: 'boolean', extends: 'checkbox' },
        { name: 'enum', extends: 'select' },
        { name: 'null', component: NullTypeComponent, wrappers: ['form-field'] },
        { name: 'array', component: ArrayTypeComponent },
        { name: 'object', component: ObjectTypeComponent },
        { name: 'multischema', component: MultiSchemaTypeComponent },
      ],
    }),
  ],
  bootstrap: [FormlyJsonComponent],
  declarations: [
    FormlyJsonComponent,
    ArrayTypeComponent,
    ObjectTypeComponent,
    MultiSchemaTypeComponent,
    NullTypeComponent,
  ],
})
export class FormlyJsonModule { }


/**  Copyright 2018 Google Inc. All Rights Reserved.
    Use of this source code is governed by an MIT-style license that
    can be found in the LICENSE file at http://angular.io/license */
