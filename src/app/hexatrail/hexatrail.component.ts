import {Component, ElementRef, Renderer2, AfterViewInit, OnChanges, SimpleChanges, NgIterable} from '@angular/core';
import {NgForOf, NgIf} from "@angular/common";


@Component({
  selector: 'hexatrail',
  templateUrl: './hexatrail.component.html',
  standalone: true,
  imports: [
    NgForOf,
    NgIf
  ],
  styleUrls: ['./hexatrail.component.scss']
})
export class HexatrailComponent implements AfterViewInit, OnChanges {
  rows: Array<any> | undefined | null;
  rowsPerPage: any;
  hexagonsPerRow: any;
  hexagonHeight: number = 110;
  hexagonWidth: number = 100;
  protected readonly length = length;
  constructor(private el: ElementRef, private renderer: Renderer2) {}

  ngAfterViewInit() {
    this.calculateRows();
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes.hasOwnProperty('hexagonClass')) {
      this.calculateRows();
    }
  }

  calculateRows() {
    const windowHeight = window.innerHeight;
    const windowWidth = window.innerWidth;
    this.rowsPerPage = Math.floor(windowHeight / this.hexagonHeight);
    this.hexagonsPerRow = Math.floor(windowWidth / this.hexagonWidth);

    length = this.rowsPerPage;
    this.rows = [];
    for (let i = 0; i < (this.hexagonsPerRow * this.rowsPerPage); i += this.rowsPerPage) {
      this.rows.push(this.hexagons[Symbol.iterator](i, i + this.rowsPerPage));
    }
  }

  get hexagons(): NodeListOf<Element> {
        return this.el.nativeElement.querySelectorAll('.hexagon');
  }
}
