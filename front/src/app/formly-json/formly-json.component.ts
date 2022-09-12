import { Component } from '@angular/core';
import { FormGroup } from '@angular/forms';
import { FormlyFormOptions, FormlyFieldConfig } from '@ngx-formly/core';
import { FormlyJsonschema } from '@ngx-formly/core/json-schema';
import { HttpClient } from '@angular/common/http';
import { tap } from 'rxjs/operators';

@Component({
  selector: 'formly-json',
  templateUrl: './formly-json.component.html',
})
export class FormlyJsonComponent {
  form!: FormGroup;
  model: any;
  options!: FormlyFormOptions;
  fields!: FormlyFieldConfig[];

  type: string | undefined;
  examples = [
    'v1',
    'v2',
    'nested',
    'arrays',
    'numbers',
    'references',
    'schema_dependencies',
    'null_field',
    'nullable',
    'allOf',
    'anyOf',
    'oneOf',
    'select_alternatives',
    'simple'
  ];

  constructor(
    private formlyJsonschema: FormlyJsonschema,
    private http: HttpClient,
  ) {
    this.loadExample(this.examples[1]);
  }

  loadExample(type: string) {
    console.log('loadExample:', type);
    this.http.get<any>(`assets/json-schema/${type}.json`).pipe(
      tap(({ schema, model }) => {
        this.type = type;
        this.form = new FormGroup({});
        this.options = {};
        this.fields = [this.formlyJsonschema.toFieldConfig(schema)];
        this.model = model;
      }),
    ).subscribe();
  }

  submit() {
    alert(JSON.stringify(this.model));
  }
}


/**  Copyright 2018 Google Inc. All Rights Reserved.
    Use of this source code is governed by an MIT-style license that
    can be found in the LICENSE file at http://angular.io/license */
