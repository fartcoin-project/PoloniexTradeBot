import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'show-data',
  templateUrl: './show-data.component.html',
  styleUrls: ['./show-data.component.scss']
})
export class ShowDataComponent implements OnInit {
  data: any;
  private req: any;
  url = '/getVol/';

  constructor(private http: HttpClient) { }

  ngOnInit() {
    this.req = this.http.get(this.url).subscribe(response => {
      console.log(response);
      this.data = response as [any];
    });
  }

  ngOnDestroy() {
    this.req.unsubscribe();
  }

}
