package main

import (
	"fmt"
	"github.com/miguelfrde/image-segmentation/graph"
	"github.com/miguelfrde/image-segmentation/segmentation"
	"html/template"
	"image"
	"image/png"
	"io"
	"math/rand"
	"mime/multipart"
	"net/http"
	"os"
	"runtime"
	"time"
)

const RANDOM_STR_SIZE = 25

var templates = template.Must(template.ParseGlob("web/templates/*"))
var letters = []byte("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789")

func randomString() string {
	chars := make([]byte, RANDOM_STR_SIZE)
	for i := range chars {
		chars[i] = letters[rand.Intn(len(letters))]
	}
	return string(chars)
}

func loadImageFromFile(filename string) image.Image {
	f, _ := os.Open(filename)
	defer f.Close()
	img, _, _ := image.Decode(f)
	return img
}

func createFileInFS(file multipart.File, extension string) (string, error) {
	defer file.Close()

	newfilename := randomString()
	imgfile, err := os.Create("tmp/" + newfilename + extension)
	if err != nil {
		return "", err
	}

	defer imgfile.Close()

	_, err = io.Copy(imgfile, file)
	if err != nil {
		return "", err
	}
	return newfilename, nil
}

/* Handlers */

func mainHandler(w http.ResponseWriter, r *http.Request) {
	templates.ExecuteTemplate(w, "main", nil)
}

func segmentHandler() {

        extension := ".jpg"
        graphType := graph.KINGSGRAPH 
        weightfn := segmentation.IntensityDifference
        //sigma := 0.30
        //minWeight := 4.05
        sigma := .20
        k := 100.0
        minsize := 100

        for i := 1; i < 253;i++ {

                filename := fmt.Sprintf("%08d", i)
                //filename := "00000130"
                fmt.Println(filename+extension)
                img := loadImageFromFile("tmp/crop_" + filename + extension)
                segmenter := segmentation.New(img, graphType, weightfn)
                //segmenter.SetRandomColors(true)
                segmenter.SegmentGBS(sigma, k, minsize)
                toimg, _ := os.Create("tmp/new_" + filename + ".png")
                defer toimg.Close()
                png.Encode(toimg, segmenter.GetResultImage())
        }
}


func main() {
	rand.Seed(time.Now().UTC().UnixNano())
	runtime.GOMAXPROCS(runtime.NumCPU())
        fmt.Println("run test")
        segmentHandler()
}
