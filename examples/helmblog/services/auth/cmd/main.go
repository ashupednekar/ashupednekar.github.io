package main

import "helmblog/services/auth/pkg"


func main(){
	s := pkg.NewServer()
	s.Start()
}
