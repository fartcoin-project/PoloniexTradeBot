export interface IRoot {
  schedule: Schedule[]
  speakers: Speaker[]
  tracks: Track[]
}

export interface Schedule {
  date: string
  groups: Group[]
}

export interface Group {
  time: string
  sessions: Session[]
}

export interface Session {
  name: string
  timeStart: string
  timeEnd: string
  location: string
  tracks: string[]
  id: string
  description?: string
  speakerNames?: string[]
}

export interface Speaker {
  name: string
  profilePic: string
  instagram: string
  twitter: string
  about: string
  title: string
  location: string
  email: string
  phone: string
  id: string
}

export interface Track {
  name: string
  icon: string
}
